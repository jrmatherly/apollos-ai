from python.helpers import files, projects, settings
from python.helpers.api import ApiHandler, Request, Response


class GetChatFilesPath(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("chats", "read_own")

    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)

        project_name = projects.get_context_project_name(context)
        if project_name:
            folder = files.normalize_a0_path(projects.get_project_folder(project_name))
        else:
            folder = settings.get_settings()["workdir_path"]

        return {
            "ok": True,
            "path": folder,
        }
