"""MCP connection pool with persistent sessions.

Manages a pool of MCP client connections keyed by server name.
Connections are reused across tool calls instead of being created/destroyed
per operation (replacing the ephemeral _execute_with_session pattern).
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

_SAFE_LOG_RE = re.compile(r"[^a-zA-Z0-9_.\-/]")


def _sanitize_log_value(value: str) -> str:
    """Sanitize user input for safe logging — allowlist alphanumeric + limited punctuation."""
    return _SAFE_LOG_RE.sub("_", value)[:128]


@dataclass
class PooledConnection:
    """Wrapper around an MCP connection with metadata."""

    server_name: str
    connection: Any  # The actual MCP client/session object
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    in_use: bool = False

    def touch(self) -> None:
        self.last_used_at = time.time()

    async def is_healthy(self) -> bool:
        """Check if the underlying connection is still usable."""
        if hasattr(self.connection, "is_healthy"):
            return await self.connection.is_healthy()
        return True


class McpConnectionPool:
    """Pool of persistent MCP connections keyed by server name.

    Usage::

        pool = McpConnectionPool(max_connections=20)
        conn = await pool.acquire("github-server", factory=create_github_conn)
        try:
            result = await conn.call_tool("search", {"query": "bugs"})
        finally:
            await pool.release("github-server")
    """

    def __init__(self, max_connections: int = 20) -> None:
        self.max_connections = max_connections
        self._connections: dict[str, PooledConnection] = {}
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def acquire(
        self,
        server_name: str,
        *,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """Get or create a connection for the given server."""
        async with self._lock:
            if server_name in self._connections:
                pooled = self._connections[server_name]
                pooled.touch()
                pooled.in_use = True
                return pooled.connection

            if self.active_count >= self.max_connections:
                await self._evict_oldest_idle()

            conn = await factory()
            self._connections[server_name] = PooledConnection(
                server_name=server_name,
                connection=conn,
                in_use=True,
            )
            logger.info(
                "Created new pooled connection for %s", _sanitize_log_value(server_name)
            )
            return conn

    async def release(self, server_name: str) -> None:
        """Mark a connection as idle (still in pool)."""
        async with self._lock:
            if server_name in self._connections:
                self._connections[server_name].in_use = False
                self._connections[server_name].touch()

    async def evict(self, server_name: str) -> None:
        """Remove and close a connection."""
        async with self._lock:
            pooled = self._connections.pop(server_name, None)
            if pooled and hasattr(pooled.connection, "close"):
                try:
                    await pooled.connection.close()
                except Exception:
                    logger.warning(
                        "Error closing connection %s",
                        _sanitize_log_value(server_name),
                    )

    async def health_check(self) -> None:
        """Check all connections and evict unhealthy ones."""
        to_evict: list[str] = []
        async with self._lock:
            for name, pooled in self._connections.items():
                if not await pooled.is_healthy():
                    to_evict.append(name)

        for name in to_evict:
            logger.warning(
                "Evicting unhealthy connection: %s", _sanitize_log_value(name)
            )
            await self.evict(name)

    async def _evict_oldest_idle(self) -> None:
        """Evict the oldest idle connection to make room (called under lock)."""
        idle = [(name, p) for name, p in self._connections.items() if not p.in_use]
        if not idle:
            logger.warning("Connection pool full, all connections in use")
            return
        idle.sort(key=lambda x: x[1].last_used_at)
        oldest_name = idle[0][0]
        pooled = self._connections.pop(oldest_name, None)
        if pooled and hasattr(pooled.connection, "close"):
            try:
                await pooled.connection.close()
            except Exception:
                pass
        logger.info(
            "Evicted idle connection %s to make room", _sanitize_log_value(oldest_name)
        )

    async def close_all(self) -> None:
        """Close all connections. Call on shutdown."""
        names = list(self._connections.keys())
        for name in names:
            await self.evict(name)
