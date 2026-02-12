"""MCP OAuth token storage and connection management (Phase 4b).

Provides two classes:

- ``VaultTokenStorage`` -- implements the MCP SDK ``TokenStorage`` protocol
  using the encrypted ``api_key_vault`` table for persistence.
- ``McpConnectionManager`` -- manages active ``ClientSession`` instances with
  dual transport support (stdio and streamable HTTP with OAuth).
"""

from __future__ import annotations

import asyncio
import json as json_mod
import logging
import os
from contextlib import AsyncExitStack
from datetime import datetime, timezone

from mcp.client.auth import OAuthClientProvider, TokenStorage  # noqa: F401 (TokenStorage for docs)
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from python.helpers import auth_db, user_store
from python.helpers.user_store import McpServiceRegistry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# VaultTokenStorage -- MCP SDK TokenStorage backed by encrypted vault
# ---------------------------------------------------------------------------


class VaultTokenStorage:
    """MCP SDK TokenStorage backed by encrypted api_key_vault."""

    def __init__(self, user_id: str, service_id: str):
        self._user_id = user_id
        self._service_id = service_id

    # -- TokenStorage protocol methods --------------------------------------

    async def get_tokens(self) -> OAuthToken | None:
        """Retrieve stored OAuth tokens from the vault."""
        try:
            with auth_db.get_session() as db:
                conn = user_store.get_connection(db, self._user_id, self._service_id)
                if not conn or not conn.access_token_vault_id:
                    return None

                access_token = user_store.get_vault_key_value(
                    db, conn.access_token_vault_id
                )

                refresh_token: str | None = None
                if conn.refresh_token_vault_id:
                    refresh_token = user_store.get_vault_key_value(
                        db, conn.refresh_token_vault_id
                    )

                expires_in: int | None = None
                if conn.token_expires_at:
                    # Ensure both datetimes are tz-aware for subtraction
                    expires_at = conn.token_expires_at
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    remaining = (
                        expires_at - datetime.now(timezone.utc)
                    ).total_seconds()
                    expires_in = max(int(remaining), 0)

                return OAuthToken(
                    access_token=access_token,
                    token_type="Bearer",
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                )
        except Exception:
            logger.exception("Failed to retrieve MCP OAuth tokens from vault")
            return None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        """Persist OAuth tokens to the vault."""
        try:
            with auth_db.get_session() as db:
                access_entry = user_store.store_vault_key(
                    db,
                    "mcp_token",
                    f"{self._user_id}:{self._service_id}",
                    "access_token",
                    tokens.access_token,
                )

                refresh_entry = None
                if tokens.refresh_token:
                    refresh_entry = user_store.store_vault_key(
                        db,
                        "mcp_token",
                        f"{self._user_id}:{self._service_id}",
                        "refresh_token",
                        tokens.refresh_token,
                    )

                token_expires_at = None
                if tokens.expires_in:
                    token_expires_at = datetime.fromtimestamp(
                        datetime.now(timezone.utc).timestamp() + tokens.expires_in,
                        tz=timezone.utc,
                    )

                user_store.upsert_connection(
                    db,
                    self._user_id,
                    self._service_id,
                    access_token_vault_id=access_entry.id,
                    refresh_token_vault_id=refresh_entry.id if refresh_entry else None,
                    token_expires_at=token_expires_at,
                )
        except Exception:
            logger.exception("Failed to store MCP OAuth tokens in vault")

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        """Retrieve stored OAuth client information from the vault."""
        try:
            with auth_db.get_session() as db:
                conn = user_store.get_connection(db, self._user_id, self._service_id)
                if not conn or not conn.client_info_vault_id:
                    return None

                client_json = user_store.get_vault_key_value(
                    db, conn.client_info_vault_id
                )
                data = json_mod.loads(client_json)
                return OAuthClientInformationFull.model_validate(data)
        except Exception:
            logger.exception("Failed to retrieve MCP OAuth client info from vault")
            return None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        """Persist OAuth client information to the vault."""
        try:
            with auth_db.get_session() as db:
                client_json = client_info.model_dump_json(exclude_none=True)
                entry = user_store.store_vault_key(
                    db,
                    "mcp_token",
                    f"{self._user_id}:{self._service_id}",
                    "client_info",
                    client_json,
                )
                user_store.upsert_connection(
                    db,
                    self._user_id,
                    self._service_id,
                    client_info_vault_id=entry.id,
                )
        except Exception:
            logger.exception("Failed to store MCP OAuth client info in vault")


# ---------------------------------------------------------------------------
# McpConnectionManager -- active ClientSession management
# ---------------------------------------------------------------------------


class McpConnectionManager:
    """Manages active MCP client sessions with stdio and HTTP transports."""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}  # key: "{user_id}:{service_id}"
        self._exit_stack = AsyncExitStack()
        self._refresh_locks: dict[str, asyncio.Lock] = {}

    async def connect(self, user_id: str, service: McpServiceRegistry) -> ClientSession:
        """Establish an MCP client session for the given service.

        Supports two transport types:
        - ``stdio``: spawns a subprocess via ``StdioServerParameters``
        - ``streamable_http``: connects over HTTP with OAuth authentication
        """
        key = f"{user_id}:{service.id}"

        if key in self._sessions:
            return self._sessions[key]

        if service.transport_type == "stdio":
            session = await self._connect_stdio(service)
        elif service.transport_type == "streamable_http":
            session = await self._connect_http(user_id, service)
        else:
            raise ValueError(f"Unknown transport type: {service.transport_type}")

        self._sessions[key] = session
        return session

    async def get_session(self, user_id: str, service_id: str) -> ClientSession | None:
        """Return an existing session or None."""
        return self._sessions.get(f"{user_id}:{service_id}")

    async def disconnect(self, user_id: str, service_id: str) -> None:
        """Remove a tracked session.

        Actual resource cleanup happens when the exit stack is closed.
        """
        key = f"{user_id}:{service_id}"
        self._sessions.pop(key, None)
        self._refresh_locks.pop(key, None)

    async def disconnect_all(self) -> None:
        """Close all transports and clear session state."""
        try:
            await self._exit_stack.aclose()
        except Exception:
            logger.exception("Error closing MCP connection exit stack")
        self._sessions.clear()
        self._refresh_locks.clear()
        self._exit_stack = AsyncExitStack()

    # -- Private helpers ----------------------------------------------------

    async def _connect_stdio(self, service: McpServiceRegistry) -> ClientSession:
        """Connect to an MCP server via stdio subprocess."""
        args = json_mod.loads(service.args_json) if service.args_json else []
        env_keys = (
            json_mod.loads(service.env_keys_json) if service.env_keys_json else []
        )

        # Resolve env keys from os.environ (placeholder for vault resolution)
        env_dict = {k: os.environ.get(k, "") for k in env_keys} if env_keys else None

        params = StdioServerParameters(
            command=service.command,
            args=args,
            env=env_dict,
        )

        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(params)
        )
        read_stream, write_stream = stdio_transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        return session

    async def _connect_http(
        self, user_id: str, service: McpServiceRegistry
    ) -> ClientSession:
        """Connect to an MCP server via streamable HTTP with OAuth."""
        storage = VaultTokenStorage(user_id, service.id)

        client_metadata = OAuthClientMetadata(
            client_name=service.name,
            redirect_uris=[
                f"{os.environ.get('APP_BASE_URL', 'http://localhost:50080')}/mcp/oauth/callback"
            ],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope=service.default_scopes or "",
        )

        oauth_auth = OAuthClientProvider(
            server_url=service.server_url,
            client_metadata=client_metadata,
            storage=storage,
            redirect_handler=self._default_redirect_handler,
            callback_handler=self._default_callback_handler,
        )

        http_transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(service.server_url, auth=oauth_auth)
        )
        read_stream, write_stream, _ = http_transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        return session

    @staticmethod
    async def _default_redirect_handler(url: str) -> None:
        """Placeholder -- actual redirect handled by API layer."""

    @staticmethod
    async def _default_callback_handler() -> tuple[str, str | None]:
        """Placeholder -- actual callback handled by Flask route."""
        raise NotImplementedError("OAuth callback must be handled by the API layer")
