from python.helpers import memory
from python.helpers.api import ApiHandler, Request, Response


class ReindexKnowledge(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("knowledge", "write")

    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)

        # reload memory to re-import knowledge
        await memory.Memory.reload(context.apollos)
        context.log.set_initial_progress()

        return {
            "ok": True,
            "message": "Knowledge re-indexed",
        }
