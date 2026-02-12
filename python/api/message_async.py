from agent import AgentContext
from python.api.message import Message
from python.helpers.defer import DeferredTask


class MessageAsync(Message):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("chats", "write")

    async def respond(self, task: DeferredTask, context: AgentContext):
        return {
            "message": "Message received.",
            "context": context.id,
        }
