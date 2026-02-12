import json
from typing import Any

from python.helpers import auth_db, user_store
from python.helpers.api import ApiHandler, Request, Response


def _connection_to_dict(conn) -> dict:
    return {
        "id": conn.id,
        "user_id": conn.user_id,
        "service_id": conn.service_id,
        "scopes_granted": conn.scopes_granted,
        "token_expires_at": conn.token_expires_at.isoformat()
        if conn.token_expires_at
        else None,
        "connected_at": conn.connected_at.isoformat() if conn.connected_at else None,
        "last_used_at": conn.last_used_at.isoformat() if conn.last_used_at else None,
        "has_access_token": bool(conn.access_token_vault_id),
        "has_refresh_token": bool(conn.refresh_token_vault_id),
    }


class McpConnections(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("mcp", "write")

    async def process(
        self, input: dict[Any, Any], request: Request
    ) -> dict[Any, Any] | Response:
        action = input.get("action", "list")
        user_id = self._get_user_id()

        if not user_id:
            return Response(
                json.dumps({"error": "Authentication required"}),
                status=401,
                mimetype="application/json",
            )

        if action == "list":
            with auth_db.get_session() as db:
                connections = user_store.list_connections(db, user_id)
                return {
                    "ok": True,
                    "data": [_connection_to_dict(c) for c in connections],
                }

        elif action == "get":
            with auth_db.get_session() as db:
                conn = user_store.get_connection(db, user_id, input["service_id"])
                if not conn:
                    return {"ok": True, "data": None}
                return {"ok": True, "data": _connection_to_dict(conn)}

        elif action == "disconnect":
            with auth_db.get_session() as db:
                user_store.delete_connection(db, user_id, input["service_id"])
                return {"ok": True}

        return Response(
            json.dumps({"error": f"Unknown action: {action}"}),
            status=400,
            mimetype="application/json",
        )
