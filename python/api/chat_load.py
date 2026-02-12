from python.helpers import persist_chat
from python.helpers.api import ApiHandler, Input, Output, Request


class LoadChats(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("chats", "read_own")

    async def process(self, input: Input, request: Request) -> Output:
        chats = input.get("chats", [])
        if not chats:
            raise Exception("No chats provided")

        tenant_ctx = self._get_tenant_ctx()
        user_id = self._get_user_id()
        ctxids = persist_chat.load_json_chats(
            chats, user_id=user_id, tenant_ctx=tenant_ctx
        )

        return {
            "message": "Chats loaded.",
            "ctxids": ctxids,
        }
