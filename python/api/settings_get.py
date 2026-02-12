from python.helpers import settings
from python.helpers.api import ApiHandler, Request, Response


class GetSettings(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("settings", "read")

    async def process(self, input: dict, request: Request) -> dict | Response:
        tenant_ctx = self._get_tenant_ctx()
        if not tenant_ctx.is_system:
            backend = settings.get_settings_for_tenant(tenant_ctx)
        else:
            backend = settings.get_settings()
        out = settings.convert_out(backend)
        return dict(out)

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
