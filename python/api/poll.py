from python.helpers.api import ApiHandler, Request, Response, g
from python.helpers.state_snapshot import build_snapshot


class Poll(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            user = g.current_user if hasattr(g, "current_user") else None
        except RuntimeError:
            user = None
        user_id = str(user["id"]) if user and "id" in user else None
        return await build_snapshot(
            context=input.get("context"),
            log_from=input.get("log_from", 0),
            notifications_from=input.get("notifications_from", 0),
            timezone=input.get("timezone"),
            user_id=user_id,
        )
