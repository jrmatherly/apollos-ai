from python.api import get_work_dir_files
from python.helpers import runtime
from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.file_browser import FileBrowser
from python.helpers.workspace import get_workspace_root


class DeleteWorkDirFile(ApiHandler):
    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("workdir", "write")

    async def process(self, input: Input, request: Request) -> Output:
        try:
            tenant_ctx = self._get_tenant_ctx()
            workspace = get_workspace_root(tenant_ctx)

            file_path = input.get("path", "")
            if not file_path.startswith("/"):
                file_path = f"/{file_path}"

            current_path = input.get("currentPath", "")

            res = await runtime.call_development_function(
                delete_file, file_path, workspace
            )

            if res:
                result = await runtime.call_development_function(
                    get_work_dir_files.get_files, current_path, workspace
                )
                return {"data": result}
            else:
                return {"error": "File not found or could not be deleted"}
        except Exception as e:
            return {"error": str(e)}


async def delete_file(file_path: str, base_dir: str):
    browser = FileBrowser(base_dir=base_dir)
    return browser.delete_file(file_path)
