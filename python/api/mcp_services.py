import json
from typing import Any

from python.helpers import auth_db, user_store
from python.helpers.api import ApiHandler, Request, Response


def _service_to_dict(svc) -> dict:
    return {
        "id": svc.id,
        "org_id": svc.org_id,
        "name": svc.name,
        "transport_type": svc.transport_type,
        "command": svc.command,
        "args_json": svc.args_json,
        "env_keys_json": svc.env_keys_json,
        "server_url": svc.server_url,
        "client_id": svc.client_id,
        "default_scopes": svc.default_scopes,
        "icon_url": svc.icon_url,
        "is_enabled": svc.is_enabled,
        "created_at": svc.created_at.isoformat() if svc.created_at else None,
    }


class McpServices(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        # Dynamic: read requires ("mcp", "read"), write requires ("admin", "mcp")
        # We handle this manually in process()
        return None

    async def process(
        self, input: dict[Any, Any], request: Request
    ) -> dict[Any, Any] | Response:
        action = input.get("action", "list")
        tenant_ctx = self._get_tenant_ctx()

        if action == "list":
            with auth_db.get_session() as db:
                org_id = input.get("org_id") or (
                    tenant_ctx.org_id if not tenant_ctx.is_system else None
                )
                services = user_store.list_services(db, org_id=org_id)
                return {"ok": True, "data": [_service_to_dict(s) for s in services]}

        # Write operations require admin permission
        user = self._get_user_id()
        if user:
            from python.helpers.rbac import check_permission

            domain = f"org:{tenant_ctx.org_id}/team:{tenant_ctx.team_id}"
            if not check_permission(user, domain, "admin", "mcp"):
                return Response(
                    json.dumps({"error": "Forbidden"}),
                    status=403,
                    mimetype="application/json",
                )

        if action == "create":
            with auth_db.get_session() as db:
                svc = user_store.create_service(
                    db,
                    name=input["name"],
                    transport_type=input.get("transport_type", "stdio"),
                    org_id=input.get("org_id"),
                    command=input.get("command"),
                    args_json=input.get("args_json", "[]"),
                    env_keys_json=input.get("env_keys_json", "[]"),
                    server_url=input.get("server_url"),
                    client_id=input.get("client_id"),
                    client_secret=input.get("client_secret"),
                    default_scopes=input.get("default_scopes"),
                    icon_url=input.get("icon_url"),
                )
                db.flush()
                return {"ok": True, "data": _service_to_dict(svc)}

        elif action == "update":
            with auth_db.get_session() as db:
                kwargs = {
                    k: v
                    for k, v in input.items()
                    if k not in ("action", "service_id") and v is not None
                }
                svc = user_store.update_service(db, input["service_id"], **kwargs)
                db.flush()
                return {"ok": True, "data": _service_to_dict(svc)}

        elif action == "delete":
            with auth_db.get_session() as db:
                user_store.delete_service(db, input["service_id"])
                return {"ok": True}

        return Response(
            json.dumps({"error": f"Unknown action: {action}"}),
            status=400,
            mimetype="application/json",
        )
