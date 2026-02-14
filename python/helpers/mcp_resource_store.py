"""MCP resource store abstraction with pluggable backends.

Inspired by Microsoft MCP Gateway's IAdapterResourceStore pattern.
Provides InMemory implementation for dev/single-instance and an ABC
for Redis/Postgres backends when horizontal scaling is needed.

Permission model: creator + admin + required_roles (from MS MCP Gateway).
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class McpServerResource:
    """Metadata for a registered MCP server."""

    name: str
    transport_type: str  # "stdio" | "streamable_http" | "sse"
    created_by: str
    url: str | None = None
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    docker_image: str | None = None
    docker_ports: dict[str, int] = field(default_factory=dict)
    required_roles: list[str] = field(default_factory=list)
    is_enabled: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def can_access(self, user_id: str, *, roles: list[str], operation: str) -> bool:
        """Check if a user can access this resource.

        Read: creator OR admin OR matching role OR no required roles.
        Write: creator OR admin only.
        """
        if user_id == self.created_by:
            return True
        if "mcp.admin" in roles:
            return True
        if operation == "read":
            if not self.required_roles:
                return True
            return any(r in self.required_roles for r in roles)
        return False  # write = creator or admin only


class McpResourceStoreBase(ABC):
    """Abstract base for MCP resource stores."""

    @abstractmethod
    def get(self, name: str) -> McpServerResource | None: ...

    @abstractmethod
    def upsert(self, resource: McpServerResource) -> None: ...

    @abstractmethod
    def delete(self, name: str) -> None: ...

    @abstractmethod
    def list_all(self) -> list[McpServerResource]: ...


class InMemoryMcpResourceStore(McpResourceStoreBase):
    """Thread-safe in-memory store for development and single-instance deployments."""

    def __init__(self) -> None:
        self._data: dict[str, McpServerResource] = {}
        self._lock = threading.Lock()

    def get(self, name: str) -> McpServerResource | None:
        with self._lock:
            return self._data.get(name)

    def upsert(self, resource: McpServerResource) -> None:
        resource.updated_at = time.time()
        with self._lock:
            self._data[resource.name] = resource

    def delete(self, name: str) -> None:
        with self._lock:
            self._data.pop(name, None)

    def list_all(self) -> list[McpServerResource]:
        with self._lock:
            return list(self._data.values())
