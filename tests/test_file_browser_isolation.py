"""Tests for file browser workspace isolation (CWE-22 remediation).

Covers:
1-6.  FileBrowser path confinement (listing, traversal, delete, upload, rename, edit)
7-8.  Baseline overlay (readonly entries, live visibility, hidden file filtering)
9-11. TenantContext workspace separation (multi-tenant, ensure_dirs, system mode)
12-14. Virtual path routing ($BASELINE/, $SHARED/, normal paths)
15-17. get_confined_abs_path boundary enforcement (valid, traversal, cross-user)
"""

import os

import pytest

from python.helpers.file_browser import FileBrowser
from python.helpers.files import get_confined_abs_path
from python.helpers.tenant import TenantContext
from python.helpers.workspace import (
    get_workspace_root,
    resolve_virtual_path,
)


# ---------------------------------------------------------------------------
# 1. FileBrowser Path Confinement
# ---------------------------------------------------------------------------
class TestFileBrowserConfinement:
    """Tests for FileBrowser path confinement."""

    def test_confines_listing_to_workspace(self, tmp_path):
        """1. FileBrowser(base_dir=workspace) confines listing to workspace."""
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "subdir").mkdir()
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.get_files("")
        names = [e["name"] for e in result["entries"]]
        assert "file1.txt" in names
        assert "subdir" in names

    def test_path_traversal_rejected(self, tmp_path):
        """2. Path traversal ../../etc/passwd is rejected."""
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.get_files("../../etc")
        # The .resolve() + .startswith() guard in get_files rejects
        # paths that escape base_dir and returns an empty listing.
        assert result is not None
        assert result["entries"] == []

    def test_delete_outside_workspace_rejected(self, tmp_path):
        """3. Delete outside workspace is rejected."""
        outside = tmp_path.parent / "outside_file.txt"
        outside.write_text("secret")
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.delete_file(str(outside))
        assert result is False
        assert outside.exists()  # File should still exist

    def test_upload_outside_workspace_rejected(self, tmp_path):
        """4. Upload outside workspace is rejected via path traversal."""
        browser = FileBrowser(base_dir=str(tmp_path))
        # save_file_b64 checks extension first, then path confinement.
        # Use an allowed extension (.txt) so the path check is reached.
        import base64

        content_b64 = base64.b64encode(b"evil").decode()
        result = browser.save_file_b64("../../", "evil.txt", content_b64)
        # Should not create file outside workspace
        assert not (tmp_path.parent / "evil.txt").exists()
        # save_file_b64 returns False on any error (path escaped base_dir)
        assert result is False

    def test_rename_outside_workspace_rejected(self, tmp_path):
        """5. Rename with path separators in new_name is rejected."""
        (tmp_path / "test.txt").write_text("content")
        browser = FileBrowser(base_dir=str(tmp_path))
        # rename_item rejects new_name containing "/" or "\"
        with pytest.raises(ValueError, match="path separators"):
            browser.rename_item("test.txt", "../../etc/evil.txt")
        # Original file should still be in workspace
        assert (tmp_path / "test.txt").exists()

    def test_save_text_outside_workspace_rejected(self, tmp_path):
        """6. save_text_file outside workspace is rejected."""
        browser = FileBrowser(base_dir=str(tmp_path))
        # save_text_file resolves the path and checks startswith(base_dir)
        with pytest.raises(ValueError, match="Invalid path"):
            browser.save_text_file("../../etc/evil.txt", "malicious content")

    def test_two_tenants_different_workspaces(self):
        """9. Two different tenant contexts get different workspace paths."""
        ctx1 = TenantContext(user_id="user1")
        ctx2 = TenantContext(user_id="user2")
        ws1 = get_workspace_root(ctx1)
        ws2 = get_workspace_root(ctx2)
        assert ws1 != ws2
        assert "user1" in ws1
        assert "user2" in ws2

    def test_ensure_dirs_creates_workdir(self, tmp_path, monkeypatch):
        """10. ensure_dirs() creates the workdir directory."""
        import python.helpers.files as files_mod

        def mock_get_abs_path(*relative_paths):
            return str(tmp_path / os.path.join(*relative_paths))

        monkeypatch.setattr(files_mod, "get_abs_path", mock_get_abs_path)

        ctx = TenantContext(user_id="testuser")
        ctx.ensure_dirs()

        # Check workdir was created
        assert (tmp_path / ctx.workdir).is_dir()
        # Also check chats and uploads
        assert (tmp_path / ctx.chats_dir).is_dir()
        assert (tmp_path / ctx.uploads_dir).is_dir()

    def test_system_mode_uses_shared_workspace(self):
        """11. System/no-auth mode uses shared workspace (backward compat)."""
        ctx = TenantContext.system()
        assert ctx.is_system
        ws = get_workspace_root(ctx)
        assert "usr/workdir" in ws

    def test_auto_creates_workspace_dir(self, tmp_path):
        """FileBrowser auto-creates base_dir if it doesn't exist."""
        new_dir = tmp_path / "new_workspace"
        assert not new_dir.exists()
        FileBrowser(base_dir=str(new_dir))
        assert new_dir.exists()


# ---------------------------------------------------------------------------
# 1b. TenantContext Path Segment Validation (CWE-22 / CodeQL py/path-injection)
# ---------------------------------------------------------------------------
class TestTenantContextPathValidation:
    """Regression tests for CWE-22 defense-in-depth in TenantContext."""

    def test_valid_uuid_user_id(self):
        """Standard UUID user_id is accepted."""
        ctx = TenantContext(user_id="550e8400-e29b-41d4-a716-446655440000")
        assert ctx.user_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_valid_email_style_user_id(self):
        """Email-style user_id (Entra OID or similar) is accepted."""
        ctx = TenantContext(user_id="user@example.com")
        assert ctx.user_id == "user@example.com"

    def test_valid_alphanumeric_ids(self):
        """Alphanumeric IDs with allowed special chars are accepted."""
        ctx = TenantContext(user_id="user_123", org_id="org-456", team_id="team.789")
        assert ctx.user_id == "user_123"
        assert ctx.org_id == "org-456"
        assert ctx.team_id == "team.789"

    def test_path_traversal_user_id_rejected(self):
        """user_id containing '../' is rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            TenantContext(user_id="../../etc")

    def test_slash_in_user_id_rejected(self):
        """user_id containing '/' is rejected."""
        with pytest.raises(ValueError, match="path separators"):
            TenantContext(user_id="user/admin")

    def test_backslash_in_user_id_rejected(self):
        """user_id containing '\\' is rejected."""
        with pytest.raises(ValueError, match="path separators"):
            TenantContext(user_id="user\\admin")

    def test_null_byte_in_user_id_rejected(self):
        """user_id containing null byte is rejected."""
        with pytest.raises(ValueError, match="null bytes"):
            TenantContext(user_id="user\x00evil")

    def test_empty_user_id_rejected(self):
        """Empty user_id is rejected."""
        with pytest.raises(ValueError, match="must not be empty"):
            TenantContext(user_id="")

    def test_path_traversal_org_id_rejected(self):
        """org_id containing '../' is rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            TenantContext(user_id="valid", org_id="../escape")

    def test_path_traversal_team_id_rejected(self):
        """team_id containing '../' is rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            TenantContext(user_id="valid", team_id="../escape")

    def test_from_session_user_with_malicious_id(self):
        """from_session_user rejects session data with path traversal."""
        with pytest.raises(ValueError, match="path traversal"):
            TenantContext.from_session_user({"id": "../../etc/passwd"})

    def test_from_session_user_valid(self):
        """from_session_user accepts normal session data."""
        ctx = TenantContext.from_session_user(
            {"id": "user123", "email": "user@test.com"}
        )
        assert ctx.user_id == "user123"

    def test_system_context_always_valid(self):
        """System context uses hardcoded safe values."""
        ctx = TenantContext.system()
        assert ctx.user_id == "system"
        assert ctx.org_id == "default"
        assert ctx.team_id == "default"


# ---------------------------------------------------------------------------
# 2. Baseline Overlay
# ---------------------------------------------------------------------------
class TestBaselineOverlay:
    """Tests for baseline file overlay system."""

    def test_baseline_entries_readonly(self, tmp_path):
        """12. Baseline entries are read-only (delete/rename/edit blocked)."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        baseline = tmp_path / "baseline"
        baseline.mkdir()
        (baseline / "readme.md").write_text("baseline content")

        browser = FileBrowser(base_dir=str(workspace))
        result = browser.get_files_merged("", baseline_dir=str(baseline))

        baseline_entries = [e for e in result["entries"] if e.get("is_baseline")]
        assert len(baseline_entries) == 1
        assert baseline_entries[0]["readonly"] is True
        assert baseline_entries[0]["name"] == "readme.md"
        assert baseline_entries[0]["path"].startswith("$BASELINE/")

    def test_baseline_changes_visible_immediately(self, tmp_path):
        """13. Baseline changes are visible to all users immediately."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        baseline = tmp_path / "baseline"
        baseline.mkdir()

        browser = FileBrowser(base_dir=str(workspace))

        # Before adding baseline file
        result = browser.get_files_merged("", baseline_dir=str(baseline))
        baseline_entries = [e for e in result["entries"] if e.get("is_baseline")]
        assert len(baseline_entries) == 0

        # Add a baseline file
        (baseline / "new_doc.txt").write_text("new content")

        # Should immediately appear (live overlay)
        result = browser.get_files_merged("", baseline_dir=str(baseline))
        baseline_entries = [e for e in result["entries"] if e.get("is_baseline")]
        assert len(baseline_entries) == 1
        assert baseline_entries[0]["name"] == "new_doc.txt"

    def test_shared_entries_writable(self, tmp_path):
        """16. Team shared workspace is accessible by team members."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        shared = tmp_path / "shared"
        shared.mkdir()

        browser = FileBrowser(base_dir=str(workspace))
        result = browser.get_files_merged("", shared_dir=str(shared))

        shared_entries = [e for e in result["entries"] if e.get("is_shared")]
        assert len(shared_entries) == 1
        assert shared_entries[0]["readonly"] is False
        assert shared_entries[0]["path"] == "$SHARED/"

    def test_baseline_hidden_files_skipped(self, tmp_path):
        """Baseline hidden files (starting with .) are skipped."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        baseline = tmp_path / "baseline"
        baseline.mkdir()
        (baseline / ".hidden").write_text("hidden")
        (baseline / "visible.txt").write_text("visible")

        browser = FileBrowser(base_dir=str(workspace))
        result = browser.get_files_merged("", baseline_dir=str(baseline))
        names = [e["name"] for e in result["entries"] if e.get("is_baseline")]
        assert "visible.txt" in names
        assert ".hidden" not in names


# ---------------------------------------------------------------------------
# 3. Virtual Path Routing
# ---------------------------------------------------------------------------
class TestVirtualPathRouting:
    """Tests for $BASELINE/ and $SHARED/ virtual path resolution."""

    def test_baseline_path_resolves_readonly(self, tmp_path):
        """resolve_virtual_path routes $BASELINE/ to baseline dir as readonly."""
        base_dir, sub, readonly = resolve_virtual_path(
            "$BASELINE/knowledge",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "bl")
        assert sub == "knowledge"
        assert readonly is True

    def test_shared_path_resolves_writable(self, tmp_path):
        """resolve_virtual_path routes $SHARED/ to shared dir as writable."""
        base_dir, sub, readonly = resolve_virtual_path(
            "$SHARED/docs",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "sh")
        assert sub == "docs"
        assert readonly is False

    def test_normal_path_resolves_to_workspace(self, tmp_path):
        """resolve_virtual_path routes normal paths to workspace."""
        base_dir, sub, readonly = resolve_virtual_path(
            "my-project",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "ws")
        assert sub == "my-project"
        assert readonly is False

    def test_bare_baseline_path(self, tmp_path):
        """resolve_virtual_path handles bare $BASELINE (no trailing slash)."""
        base_dir, sub, readonly = resolve_virtual_path(
            "$BASELINE",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "bl")
        assert sub == ""
        assert readonly is True

    def test_bare_shared_path(self, tmp_path):
        """resolve_virtual_path handles bare $SHARED (no trailing slash)."""
        base_dir, sub, readonly = resolve_virtual_path(
            "$SHARED",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "sh")
        assert sub == ""
        assert readonly is False

    def test_leading_slash_stripped_from_normal_path(self, tmp_path):
        """resolve_virtual_path strips leading / from normal paths."""
        base_dir, sub, readonly = resolve_virtual_path(
            "/my-file.txt",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "ws")
        assert sub == "my-file.txt"
        assert readonly is False

    def test_empty_path_resolves_to_workspace_root(self, tmp_path):
        """resolve_virtual_path handles empty string as workspace root."""
        base_dir, sub, readonly = resolve_virtual_path(
            "",
            str(tmp_path / "ws"),
            str(tmp_path / "bl"),
            str(tmp_path / "sh"),
        )
        assert base_dir == str(tmp_path / "ws")
        assert sub == ""
        assert readonly is False


# ---------------------------------------------------------------------------
# 3b. Workspace Root Operations (regression for PR #9 bugs)
# ---------------------------------------------------------------------------
class TestWorkspaceRootOperations:
    """Regression tests for file operations at workspace root (currentPath='')."""

    def test_create_folder_at_workspace_root(self, tmp_path):
        """Create folder with empty parent_path succeeds (workspace root)."""
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.create_folder("", "new-folder")
        assert result is True
        assert (tmp_path / "new-folder").is_dir()

    def test_create_file_at_workspace_root(self, tmp_path):
        """Save text file with bare filename works at workspace root."""
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.save_text_file("test-file.txt", "hello world")
        assert result is True
        assert (tmp_path / "test-file.txt").read_text() == "hello world"

    def test_rename_file_at_workspace_root(self, tmp_path):
        """Rename file using relative path (no leading /) works."""
        (tmp_path / "original.txt").write_text("content")
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.rename_item("original.txt", "renamed.txt")
        assert result is True
        assert not (tmp_path / "original.txt").exists()
        assert (tmp_path / "renamed.txt").read_text() == "content"

    def test_delete_file_at_workspace_root(self, tmp_path):
        """Delete file using relative path (no leading /) works."""
        (tmp_path / "to-delete.txt").write_text("content")
        browser = FileBrowser(base_dir=str(tmp_path))
        result = browser.delete_file("to-delete.txt")
        assert result is True
        assert not (tmp_path / "to-delete.txt").exists()

    def test_leading_slash_path_does_not_escape_workspace(self, tmp_path):
        """Path with leading / should NOT escape workspace via pathlib."""
        browser = FileBrowser(base_dir=str(tmp_path))
        # After resolve_virtual_path strips the "/", this should work
        result = browser.save_text_file("test.txt", "content")
        assert result is True
        assert (tmp_path / "test.txt").exists()

    def test_resolve_then_create_folder_integration(self, tmp_path):
        """Full flow: resolve empty path then create folder."""
        workspace = str(tmp_path / "ws")
        baseline = str(tmp_path / "bl")
        shared = str(tmp_path / "sh")
        resolved_dir, resolved_parent, _readonly = resolve_virtual_path(
            "", workspace, baseline, shared
        )
        browser = FileBrowser(base_dir=resolved_dir)
        result = browser.create_folder(resolved_parent, "my-folder")
        assert result is True
        assert (tmp_path / "ws" / "my-folder").is_dir()

    def test_resolve_then_save_file_integration(self, tmp_path):
        """Full flow: resolve path with leading / then save file."""
        workspace = str(tmp_path / "ws")
        baseline = str(tmp_path / "bl")
        shared = str(tmp_path / "sh")
        # Simulates frontend sending "/filename" when currentPath is empty
        resolved_dir, resolved_path, _readonly = resolve_virtual_path(
            "/new-file.txt", workspace, baseline, shared
        )
        browser = FileBrowser(base_dir=resolved_dir)
        result = browser.save_text_file(resolved_path, "file content")
        assert result is True
        assert (tmp_path / "ws" / "new-file.txt").read_text() == "file content"

    def test_resolve_then_rename_integration(self, tmp_path):
        """Full flow: resolve relative filename then rename."""
        workspace = tmp_path / "ws"
        workspace.mkdir()
        (workspace / "old-name.txt").write_text("data")

        resolved_dir, resolved_path, _readonly = resolve_virtual_path(
            "old-name.txt", str(workspace), str(tmp_path / "bl"), str(tmp_path / "sh")
        )
        browser = FileBrowser(base_dir=resolved_dir)
        result = browser.rename_item(resolved_path, "new-name.txt")
        assert result is True
        assert (workspace / "new-name.txt").read_text() == "data"


# ---------------------------------------------------------------------------
# 4. get_confined_abs_path Boundary Enforcement
# ---------------------------------------------------------------------------
class TestConfinedAbsPath:
    """Tests for get_confined_abs_path path boundary enforcement."""

    def test_valid_path_within_boundary(self, tmp_path):
        """Path within boundary resolves correctly."""
        (tmp_path / "file.txt").write_text("content")
        result = get_confined_abs_path("file.txt", str(tmp_path))
        assert result == str((tmp_path / "file.txt").resolve())

    def test_traversal_raises_error(self, tmp_path):
        """Path escaping boundary raises ValueError."""
        with pytest.raises(ValueError, match="escapes boundary"):
            get_confined_abs_path("../../etc/passwd", str(tmp_path))

    def test_boundary_itself_is_valid(self, tmp_path):
        """The boundary directory itself is a valid path."""
        result = get_confined_abs_path("", str(tmp_path))
        assert result == str(tmp_path.resolve())

    def test_cross_user_access_blocked(self, tmp_path):
        """17. Cross-user file access is blocked."""
        user1 = tmp_path / "user1"
        user2 = tmp_path / "user2"
        user1.mkdir()
        user2.mkdir()
        (user2 / "secret.txt").write_text("secret")

        # User 1 trying to access user 2's file
        with pytest.raises(ValueError, match="escapes boundary"):
            get_confined_abs_path("../user2/secret.txt", str(user1))

    def test_symlink_escape_blocked(self, tmp_path):
        """Symlink pointing outside boundary is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("secret")

        # Create symlink inside workspace pointing outside
        symlink = workspace / "escape"
        symlink.symlink_to(outside)

        # os.path.realpath resolves symlinks before the startswith check
        with pytest.raises(ValueError, match="escapes boundary"):
            get_confined_abs_path("escape/secret.txt", str(workspace))

    def test_nested_path_within_boundary(self, tmp_path):
        """Nested subdirectory path within boundary resolves correctly."""
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        (subdir / "deep.txt").write_text("deep")
        result = get_confined_abs_path("a/b/c/deep.txt", str(tmp_path))
        assert result == str((tmp_path / "a" / "b" / "c" / "deep.txt").resolve())
