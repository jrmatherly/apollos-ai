from typing import Any

from python.helpers import settings
from python.helpers.api import ApiHandler, Request, Response


class SetSettings(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("settings", "write")

    async def process(
        self, input: dict[Any, Any], request: Request
    ) -> dict[Any, Any] | Response:
        frontend = input.get("settings", input)
        backend = settings.convert_in(settings.Settings(**frontend))
        tenant_ctx = self._get_tenant_ctx()
        if not tenant_ctx.is_system:
            backend = settings.set_settings_for_tenant(backend, tenant_ctx)
        else:
            backend = settings.set_settings(backend)
        out = settings.convert_out(backend)
        return dict(out)
