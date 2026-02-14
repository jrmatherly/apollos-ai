"""Docker container lifecycle manager for MCP servers.

Extends patterns from ``python/helpers/docker.py`` (used for code execution
sandboxes) to manage MCP server containers. Each MCP server runs in its own
container with a standardized naming convention and health checking.
"""

from __future__ import annotations

import logging
from typing import Any

from python.helpers.mcp_resource_store import McpServerResource

import docker

logger = logging.getLogger(__name__)

# Container name prefix for all MCP server containers
_CONTAINER_PREFIX = "apollos-mcp-"


class McpContainerManager:
    """Manage MCP server Docker containers."""

    def __init__(self) -> None:
        self.client: docker.DockerClient = docker.from_env()

    def _container_name(self, server_name: str) -> str:
        return f"{_CONTAINER_PREFIX}{server_name}"

    def _find_container(self, server_name: str) -> Any | None:
        """Find an existing container by server name."""
        target_name = self._container_name(server_name)
        for container in self.client.containers.list(all=True):
            if container.name == target_name:
                return container
        return None

    def start_server(self, resource: McpServerResource) -> str:
        """Start an MCP server container. Returns container ID.

        If a container with the same name already exists and is running,
        returns its ID. If stopped, restarts it. If not found, creates new.
        """
        existing = self._find_container(resource.name)

        if existing:
            if existing.status != "running":
                logger.info("Starting stopped MCP container: %s", resource.name)
                existing.start()
            return existing.id

        if not resource.docker_image:
            raise ValueError(
                f"MCP server '{resource.name}' has no docker_image configured"
            )

        name = self._container_name(resource.name)
        logger.info(
            "Creating MCP container: %s (image: %s)", name, resource.docker_image
        )

        container = self.client.containers.run(
            resource.docker_image,
            detach=True,
            name=name,
            ports=resource.docker_ports or None,
            environment=resource.env or None,
            restart_policy={"Name": "unless-stopped"},
            labels={
                "apollos.mcp.server": resource.name,
                "apollos.mcp.transport": resource.transport_type,
                "apollos.mcp.created_by": resource.created_by,
            },
        )
        logger.info("Started MCP container %s (ID: %s)", name, container.id)
        return container.id

    def stop_server(self, server_name: str) -> None:
        """Stop and remove an MCP server container."""
        container = self._find_container(server_name)
        if not container:
            logger.warning("No container found for MCP server: %s", server_name)
            return
        logger.info("Stopping MCP container: %s", server_name)
        container.stop()
        container.remove()

    def get_status(self, server_name: str) -> dict[str, Any]:
        """Get the status of an MCP server container."""
        container = self._find_container(server_name)
        if not container:
            return {"running": False, "container_id": None, "status": "not_found"}
        return {
            "running": container.status == "running",
            "container_id": container.id,
            "status": container.status,
        }

    def get_logs(self, server_name: str, tail: int = 100) -> str:
        """Get recent logs from an MCP server container."""
        container = self._find_container(server_name)
        if not container:
            return ""
        return container.logs(tail=tail).decode("utf-8", errors="replace")

    def list_servers(self) -> list[dict[str, Any]]:
        """List all MCP server containers."""
        results = []
        for container in self.client.containers.list(
            all=True, filters={"label": "apollos.mcp.server"}
        ):
            results.append(
                {
                    "name": container.labels.get("apollos.mcp.server", ""),
                    "container_id": container.id,
                    "status": container.status,
                    "image": str(container.image),
                    "transport": container.labels.get("apollos.mcp.transport", ""),
                }
            )
        return results
