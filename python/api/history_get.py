from python.helpers.api import ApiHandler, Request, Response


class GetHistory(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("chats", "read_own")

    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", [])
        context = self.use_context(ctxid)
        agent = context.streaming_agent or context.apollos
        history = agent.history.output_text()
        size = agent.history.get_tokens()

        return {"history": history, "tokens": size}
