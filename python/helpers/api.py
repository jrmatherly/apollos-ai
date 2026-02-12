import json
import threading
from abc import abstractmethod
from typing import Any, Dict, TypedDict, Union

from flask import (  # noqa: F401 — send_file, session re-exported for API handlers
    Flask,
    Request,
    Response,
    g,
    send_file,
    session,
)

from agent import AgentContext
from initialize import initialize_agent
from python.helpers import runtime
from python.helpers.errors import format_error
from python.helpers.print_style import PrintStyle
from python.helpers.tenant import SYSTEM_USER_ID, TenantContext

ThreadLockType = Union[threading.Lock, threading.RLock]

Input = dict
Output = Union[Dict[str, Any], Response, TypedDict]  # type: ignore


class ApiHandler:
    def __init__(self, app: Flask, thread_lock: ThreadLockType):
        self.app = app
        self.thread_lock = thread_lock

    @classmethod
    def requires_loopback(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return cls.requires_auth()

    @abstractmethod
    async def process(self, input: Input, request: Request) -> Output:
        pass

    async def handle_request(self, request: Request) -> Response:
        try:
            # Populate g.current_user from session for downstream handlers
            g.current_user = session.get("user")

            # input data from request based on type
            input_data: Input = {}
            if request.is_json:
                try:
                    if request.data:  # Check if there's any data
                        input_data = request.get_json()
                    # If empty or not valid JSON, use empty dict
                except Exception as e:
                    # Just log the error and continue with empty input
                    PrintStyle().print(f"Error parsing JSON: {str(e)}")
                    input_data = {}
            else:
                # input_data = {"data": request.get_data(as_text=True)}
                input_data = {}

            # process via handler
            output = await self.process(input_data, request)

            # return output based on type
            if isinstance(output, Response):
                return output
            else:
                response_json = json.dumps(output)
                return Response(
                    response=response_json, status=200, mimetype="application/json"
                )

            # return exceptions with 500
        except Exception as e:
            error = format_error(e)
            PrintStyle.error(f"API error: {error}")
            if runtime.is_development():
                return Response(response=error, status=500, mimetype="text/plain")
            else:
                return Response(
                    response=json.dumps({"error": "Internal server error"}),
                    status=500,
                    mimetype="application/json",
                )

    def _get_tenant_ctx(self) -> TenantContext:
        """Build TenantContext from g.current_user (set by handle_request)."""
        try:
            user = g.current_user if hasattr(g, "current_user") else None
        except RuntimeError:
            user = None
        return TenantContext.from_session_user(user)

    def _get_user_id(self) -> str | None:
        """Return user_id from g.current_user, or None for no-auth."""
        try:
            user = g.current_user if hasattr(g, "current_user") else None
        except RuntimeError:
            user = None
        if user:
            return str(user.get("id", SYSTEM_USER_ID))
        return None

    # get context to run apollos ai in
    def use_context(self, ctxid: str, create_if_not_exists: bool = True):
        tenant_ctx = self._get_tenant_ctx()
        user_id = self._get_user_id()

        with self.thread_lock:
            if not ctxid:
                # Find first context for this user, or create one
                first = (
                    AgentContext.first_for_user(user_id)
                    if user_id
                    else AgentContext.first()
                )
                if first:
                    AgentContext.use(first.id)
                    return first
                context = AgentContext(
                    config=initialize_agent(tenant_ctx=tenant_ctx),
                    set_current=True,
                    user_id=user_id,
                    tenant_ctx=tenant_ctx,
                )
                tenant_ctx.ensure_dirs()
                return context
            got = AgentContext.use(ctxid)
            if got:
                # Ownership check: non-system users can only access their own contexts
                if user_id and got.user_id and got.user_id != user_id:
                    raise Exception(f"Access denied to context {ctxid}")
                return got
            if create_if_not_exists:
                context = AgentContext(
                    config=initialize_agent(tenant_ctx=tenant_ctx),
                    id=ctxid,
                    set_current=True,
                    user_id=user_id,
                    tenant_ctx=tenant_ctx,
                )
                tenant_ctx.ensure_dirs()
                return context
            else:
                raise Exception(f"Context {ctxid} not found")
