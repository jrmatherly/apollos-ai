# Workspace Root Path Fix (Feb 2026)

## Problem
After PR #9 (workspace isolation), file operations at workspace root failed:
- Create folder: "Parent path is required" (empty string falsy check)
- Create file: "Invalid path" (leading "/" broke pathlib joining)
- Rename: "Invalid path" (same pathlib issue)
- Upload worked (different code path, no "/" prepend)

## Root Causes
1. `rename_work_dir_file.py:34` — `if not parent_path:` treated `""` (workspace root) as missing
2. API endpoints (`edit_`, `rename_`, `delete_`, `download_work_dir_file.py`) prepended "/" to resolved paths. In Python, `Path(base) / "/file"` treats "/file" as absolute, replacing base entirely. The traversal safety check then correctly rejected the escaped path.

## Fix
1. `workspace.py` — `resolve_virtual_path` else branch: `current_path.lstrip("/")`
2. Removed `if not resolved_path.startswith("/"): resolved_path = f"/{resolved_path}"` from all 4 API endpoints
3. Changed `if not parent_path:` to `if parent_path is None:` in create-folder

## Tests Added
10 regression tests in `TestWorkspaceRootOperations` + 2 in `TestVirtualPathRouting`:
- Create folder/file/rename/delete at workspace root
- Leading "/" path doesn't escape workspace
- Integration tests: resolve_virtual_path → FileBrowser operation
