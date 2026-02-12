from python.helpers import process
from python.helpers.api import ApiHandler, Request, Response


class Restart(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("admin", "system")

    async def process(self, input: dict, request: Request) -> dict | Response:
        process.reload()
        return Response(status=200)
