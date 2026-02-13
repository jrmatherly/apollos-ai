"""Workspace resolution helpers for per-user file browser isolation."""

from python.helpers import files
from python.helpers.tenant import TenantContext

BASELINE_DIR = "usr/baseline"


def get_workspace_root(tenant_ctx: TenantContext) -> str:
    """Resolve absolute workspace path for the current user."""
    if tenant_ctx.is_system:
        return files.get_abs_path("usr/workdir")
    return files.get_abs_path(tenant_ctx.workdir)


def get_baseline_root() -> str:
    """Resolve absolute path to admin-managed baseline directory."""
    return files.get_abs_path(BASELINE_DIR)


def get_team_shared_root(tenant_ctx: TenantContext) -> str:
    """Resolve absolute path to team shared workspace."""
    if tenant_ctx.is_system:
        return files.get_abs_path("usr/shared")
    return files.get_abs_path(f"{tenant_ctx.team_dir}/shared")


def is_admin_user(tenant_ctx: TenantContext) -> bool:
    """Check if user has admin workspace access (RBAC integration point)."""
    # TODO: Wire to actual RBAC check via casbin
    return False
