# CodeQL Path Injection Fix (Feb 2026)

## Alerts
- #71, #72: `py/path-injection` (high severity) on `file_browser.py:25-26`
- Rule: CWE-22 — Uncontrolled data used in path expression

## Taint Chain
```
session["user"]["id"] → TenantContext.from_session_user() → tenant_ctx.workdir
  → f"usr/orgs/{org_id}/teams/{team_id}/members/{user_id}/workdir"
  → files.get_abs_path() → FileBrowser(base_dir=...) → os.makedirs() [sink]
```

## Fix: Defense-in-Depth at TenantContext
- Added `_validate_path_segment()` in `tenant.py`
- Called in `TenantContext.__post_init__()` on user_id, org_id, team_id
- Rejects: `../`, `/`, `\`, null bytes, empty strings, control chars
- Allows: `[a-zA-Z0-9._@-]+` (covers UUIDs, emails, slugs)
- Breaks the taint chain before any path construction

## Tests
13 tests in `TestTenantContextPathValidation`:
- Valid: UUID, email-style, alphanumeric with allowed special chars
- Rejected: path traversal, slashes, backslashes, null bytes, empty
- Integration: from_session_user with malicious data, system context
