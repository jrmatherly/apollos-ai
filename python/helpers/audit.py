"""Audit logging for security-relevant events.

Writes structured audit entries to the auth database.  Events include
logins, login failures, MCP tool invocations, and admin actions.

Usage::

    from python.helpers.audit import create_audit_entry

    await create_audit_entry(
        user_id="abc-123",
        action="login",
        resource="/login",
        details={"method": "oidc"},
        ip="10.0.0.1",
    )

.. warning::
    Never include tokens, secrets, or credentials in *details*.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from python.helpers import auth_db
from python.helpers.auth_db import Base
from python.helpers.print_style import PrintStyle


class AuditLog(Base):
    """Immutable audit log entry."""

    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


async def create_audit_entry(
    user_id: str | None,
    action: str,
    resource: str | None = None,
    details: dict | None = None,
    ip: str | None = None,
) -> None:
    """Write an audit log entry to auth.db.

    This is intentionally fire-and-forget — audit failures should never
    break the main request path.
    """
    try:
        with auth_db.get_session() as db:
            entry = AuditLog(
                id=str(uuid4()),
                user_id=user_id,
                action=action,
                resource=resource,
                details_json=json.dumps(details) if details else None,
                ip_address=ip,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(entry)
    except Exception as e:
        PrintStyle.error(f"Audit log write failed: {e}")
