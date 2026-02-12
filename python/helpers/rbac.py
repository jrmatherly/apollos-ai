"""Role-Based Access Control (RBAC) using Casbin.

Provides a lazy-initialized Casbin enforcer backed by the auth database
(via ``casbin-sqlalchemy-adapter``).  Roles are assigned globally via the
``g`` grouping function, while domain-scoped permissions are enforced
through ``p`` policy rules with ``keyMatch`` wildcard patterns.

The model uses ``g = _, _`` (no domain in grouping) because pycasbin's
default role manager does not support domain-scoped ``has_link``.  Domain
matching is handled entirely in the matchers via ``keyMatch(r.dom, p.dom)``.

Usage::

    from python.helpers.rbac import init_enforcer, check_permission, sync_user_roles

    # At startup
    init_enforcer()

    # On login
    sync_user_roles(user_id)

    # Per-request
    allowed = check_permission(user_id, domain, resource, action)
"""

import casbin

from python.helpers import auth_db, user_store
from python.helpers.files import get_abs_path
from python.helpers.print_style import PrintStyle

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_enforcer: casbin.Enforcer | None = None

_RBAC_MODEL_PATH = "conf/rbac_model.conf"


def init_enforcer() -> casbin.Enforcer:
    """Initialize the Casbin enforcer (lazy singleton).

    Creates the enforcer from the RBAC model file and a SQLAlchemy adapter
    sharing the auth database engine.  Safe to call multiple times.
    """
    global _enforcer  # noqa: PLW0603

    if _enforcer is not None:
        return _enforcer

    from casbin_sqlalchemy_adapter import Adapter

    engine = auth_db.get_engine()
    adapter = Adapter(engine)

    model_path = get_abs_path(_RBAC_MODEL_PATH)
    _enforcer = casbin.Enforcer(model_path, adapter)

    PrintStyle.info("RBAC enforcer initialized")
    return _enforcer


def get_enforcer() -> casbin.Enforcer:
    """Return the cached Casbin enforcer.

    Raises:
        RuntimeError: If :func:`init_enforcer` has not been called.
    """
    if _enforcer is None:
        raise RuntimeError("RBAC enforcer not initialized. Call init_enforcer() first.")
    return _enforcer


# ---------------------------------------------------------------------------
# Permission checking
# ---------------------------------------------------------------------------


def check_permission(user_id: str, domain: str, resource: str, action: str) -> bool:
    """Check whether a user has permission in the given domain.

    Args:
        user_id: The user's primary key (string UUID or EntraID oid).
        domain: Tenant domain, e.g. ``"org:acme/team:eng"``.
        resource: Resource name, e.g. ``"chats"``, ``"settings"``.
        action: Action name, e.g. ``"read"``, ``"write"``, ``"create"``.

    Returns:
        True if the user is allowed, False otherwise.
    """
    enforcer = get_enforcer()
    return enforcer.enforce(user_id, domain, resource, action)


# ---------------------------------------------------------------------------
# Role synchronization (called on login)
# ---------------------------------------------------------------------------


def sync_user_roles(user_id: str) -> None:
    """Sync a user's DB memberships to Casbin grouping policies.

    Reads the user's org and team memberships from the auth database and
    replaces their Casbin ``g`` policies accordingly.  Roles are assigned
    globally (no domain in grouping) — domain scoping is handled by the
    ``p`` policy rules.
    """
    enforcer = get_enforcer()

    # Remove all existing grouping policies for this user
    enforcer.remove_filtered_grouping_policy(0, user_id)

    roles_added: set[str] = set()

    with auth_db.get_session() as db:
        user = user_store.get_user_by_id(db, user_id)
        if user is None:
            return

        # System admin role
        if user.is_system_admin:
            enforcer.add_grouping_policy(user_id, "system_admin")
            roles_added.add("system_admin")

        # Org memberships
        for om in user.org_memberships:
            role = _map_org_role(om.role)
            if role not in roles_added:
                enforcer.add_grouping_policy(user_id, role)
                roles_added.add(role)

        # Team memberships
        for tm in user.team_memberships:
            role = _map_team_role(tm.role)
            if role not in roles_added:
                enforcer.add_grouping_policy(user_id, role)
                roles_added.add(role)


def _map_org_role(db_role: str) -> str:
    """Map auth DB org membership role to Casbin role name."""
    return {
        "owner": "org_owner",
        "admin": "org_admin",
        "member": "member",
    }.get(db_role, "member")


def _map_team_role(db_role: str) -> str:
    """Map auth DB team membership role to Casbin role name."""
    return {
        "lead": "team_lead",
        "member": "member",
        "viewer": "viewer",
    }.get(db_role, "member")


# ---------------------------------------------------------------------------
# Default policy seeding
# ---------------------------------------------------------------------------

# (role, domain_pattern, resource, action)
_DEFAULT_POLICIES: list[tuple[str, str, str, str]] = [
    # system_admin: full access to everything
    ("system_admin", "*", "*", "*"),
    # org_owner: full access within their org
    ("org_owner", "org:*", "*", "*"),
    # org_admin: manage org-level resources
    ("org_admin", "org:*", "settings", "*"),
    ("org_admin", "org:*", "admin", "*"),
    ("org_admin", "org:*", "mcp", "*"),
    ("org_admin", "org:*", "knowledge", "*"),
    # team_lead: full access within their team scope
    ("team_lead", "org:*/team:*", "chats", "*"),
    ("team_lead", "org:*/team:*", "settings", "read"),
    ("team_lead", "org:*/team:*", "knowledge", "*"),
    ("team_lead", "org:*/team:*", "memory", "*"),
    ("team_lead", "org:*/team:*", "scheduler", "*"),
    ("team_lead", "org:*/team:*", "workdir", "*"),
    ("team_lead", "org:*/team:*", "mcp", "read"),
    ("team_lead", "org:*/team:*", "mcp", "execute"),
    ("team_lead", "org:*/team:*", "notifications", "*"),
    ("team_lead", "org:*/team:*", "projects", "read"),
    ("team_lead", "org:*/team:*", "skills", "*"),
    ("team_lead", "org:*/team:*", "agents", "read"),
    ("team_lead", "org:*/team:*", "system", "read"),
    # member: standard access
    ("member", "org:*/team:*", "chats", "create"),
    ("member", "org:*/team:*", "chats", "read_own"),
    ("member", "org:*/team:*", "chats", "write"),
    ("member", "org:*/team:*", "chats", "delete"),
    ("member", "org:*/team:*", "settings", "read"),
    ("member", "org:*/team:*", "settings", "write"),
    ("member", "org:*/team:*", "knowledge", "read"),
    ("member", "org:*/team:*", "knowledge", "upload"),
    ("member", "org:*/team:*", "knowledge", "write"),
    ("member", "org:*/team:*", "memory", "read"),
    ("member", "org:*/team:*", "scheduler", "manage_own"),
    ("member", "org:*/team:*", "workdir", "read"),
    ("member", "org:*/team:*", "workdir", "write"),
    ("member", "org:*/team:*", "mcp", "read"),
    ("member", "org:*/team:*", "mcp", "write"),
    ("member", "org:*/team:*", "mcp", "execute"),
    ("member", "org:*/team:*", "notifications", "read"),
    ("member", "org:*/team:*", "notifications", "write"),
    ("member", "org:*/team:*", "projects", "read"),
    ("member", "org:*/team:*", "skills", "read"),
    ("member", "org:*/team:*", "skills", "write"),
    ("member", "org:*/team:*", "agents", "read"),
    ("member", "org:*/team:*", "system", "read"),
    # viewer: read-only access
    ("viewer", "org:*/team:*", "chats", "read_own"),
    ("viewer", "org:*/team:*", "settings", "read"),
    ("viewer", "org:*/team:*", "knowledge", "read"),
    ("viewer", "org:*/team:*", "memory", "read"),
    ("viewer", "org:*/team:*", "workdir", "read"),
    ("viewer", "org:*/team:*", "mcp", "read"),
    ("viewer", "org:*/team:*", "notifications", "read"),
    ("viewer", "org:*/team:*", "projects", "read"),
    ("viewer", "org:*/team:*", "skills", "read"),
    ("viewer", "org:*/team:*", "agents", "read"),
    ("viewer", "org:*/team:*", "system", "read"),
]


def seed_default_policies() -> None:
    """Idempotently seed the default RBAC policy rules.

    Checks for each rule before adding to avoid duplicates on repeated
    bootstrap calls.
    """
    enforcer = get_enforcer()

    added = 0
    for role, domain, resource, action in _DEFAULT_POLICIES:
        if not enforcer.has_policy(role, domain, resource, action):
            enforcer.add_policy(role, domain, resource, action)
            added += 1

    if added:
        PrintStyle.info(f"RBAC: seeded {added} default policy rules")
    else:
        PrintStyle.info("RBAC: default policies already present")
