from python.helpers import runtime
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.file_browser import FileBrowser
from python.helpers.workspace import (
    get_baseline_root,
    get_team_shared_root,
    get_workspace_root,
    resolve_virtual_path,
)

_VIRTUAL_PREFIXES = ("$PROJECTS/", "$BASELINE/", "$SHARED/")


def _get_virtual_prefix(path: str) -> str:
    """Extract the virtual prefix from a path, if any."""
    for pfx in _VIRTUAL_PREFIXES:
        if path.startswith(pfx) or path == pfx.rstrip("/"):
            return pfx
    return ""


def _prefix_response_paths(result: dict, prefix: str) -> dict:
    """Re-prefix response paths so the frontend preserves virtual context."""
    cp = result.get("current_path", "")
    if cp:
        result["current_path"] = prefix + cp

    pp = result.get("parent_path", "")
    if pp and pp != ".":
        result["parent_path"] = prefix + pp
    elif pp == ".":
        # At virtual root — parent is workspace root
        result["parent_path"] = ""

    for entry in result.get("entries", []):
        if entry.get("path"):
            entry["path"] = prefix + entry["path"]

    return result


class GetWorkDirFiles(ApiHandler):
    @classmethod
    def get_methods(cls):
        return ["GET"]

    @classmethod
    def get_required_permission(cls) -> tuple[str, str] | None:
        return ("workdir", "read")

    async def process(self, input: dict, request: Request) -> dict | Response:
        tenant_ctx = self._get_tenant_ctx()
        workspace = get_workspace_root(tenant_ctx)
        baseline_dir = get_baseline_root()
        shared_dir = get_team_shared_root(tenant_ctx)

        current_path = request.args.get("path", "")
        if current_path == "$WORK_DIR":
            current_path = ""

        # At workspace root, return merged view with baseline and shared entries
        if not current_path:
            result = await runtime.call_development_function(
                get_files_merged, current_path, workspace, baseline_dir, shared_dir
            )
            return {"data": result}

        # Detect virtual prefix for re-prefixing response paths
        prefix = _get_virtual_prefix(current_path)

        # Route virtual path prefixes to the correct directory
        resolved_dir, sub_path, _readonly = resolve_virtual_path(
            current_path, workspace, baseline_dir, shared_dir
        )

        result = await runtime.call_development_function(
            get_files, sub_path, resolved_dir
        )

        # Re-prefix paths so frontend preserves virtual context during navigation
        if prefix:
            result = _prefix_response_paths(result, prefix)

        return {"data": result}


async def get_files_merged(path, base_dir, baseline_dir, shared_dir):
    browser = FileBrowser(base_dir=base_dir)
    return browser.get_files_merged(
        path, baseline_dir=baseline_dir, shared_dir=shared_dir
    )


async def get_files(path, base_dir):
    browser = FileBrowser(base_dir=base_dir)
    return browser.get_files(path)
