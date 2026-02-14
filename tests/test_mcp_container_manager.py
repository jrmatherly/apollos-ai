"""Tests for MCP server Docker container lifecycle management."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_docker():
    """Mock docker.from_env() to avoid requiring Docker daemon."""
    with patch("docker.from_env") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestMcpContainerManager:
    def test_init_creates_client(self, mock_docker):
        from python.helpers.mcp_container_manager import McpContainerManager

        mgr = McpContainerManager()
        assert mgr.client is not None

    def test_start_server_creates_container(self, mock_docker):
        from python.helpers.mcp_container_manager import McpContainerManager
        from python.helpers.mcp_resource_store import McpServerResource

        mock_docker.containers.list.return_value = []
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.status = "running"
        mock_docker.containers.run.return_value = mock_container

        mgr = McpContainerManager()
        resource = McpServerResource(
            name="test-mcp",
            transport_type="streamable_http",
            created_by="admin",
            docker_image="mcp/test:latest",
            docker_ports={"8000/tcp": 9001},
        )
        container_id = mgr.start_server(resource)
        assert container_id == "abc123"
        mock_docker.containers.run.assert_called_once()

    def test_start_server_reuses_existing(self, mock_docker):
        from python.helpers.mcp_container_manager import McpContainerManager
        from python.helpers.mcp_resource_store import McpServerResource

        existing = MagicMock()
        existing.name = "apollos-mcp-test-mcp"
        existing.id = "existing123"
        existing.status = "running"
        mock_docker.containers.list.return_value = [existing]

        mgr = McpContainerManager()
        resource = McpServerResource(
            name="test-mcp",
            transport_type="streamable_http",
            created_by="admin",
            docker_image="mcp/test:latest",
        )
        container_id = mgr.start_server(resource)
        assert container_id == "existing123"
        mock_docker.containers.run.assert_not_called()

    def test_stop_server(self, mock_docker):
        from python.helpers.mcp_container_manager import McpContainerManager

        container = MagicMock()
        container.name = "apollos-mcp-my-server"
        mock_docker.containers.list.return_value = [container]

        mgr = McpContainerManager()
        mgr.stop_server("my-server")
        container.stop.assert_called_once()
        container.remove.assert_called_once()

    def test_get_status_running(self, mock_docker):
        from python.helpers.mcp_container_manager import McpContainerManager

        container = MagicMock()
        container.name = "apollos-mcp-my-server"
        container.status = "running"
        container.id = "xyz"
        mock_docker.containers.list.return_value = [container]

        mgr = McpContainerManager()
        status = mgr.get_status("my-server")
        assert status["running"] is True
        assert status["container_id"] == "xyz"

    def test_get_status_not_found(self, mock_docker):
        from python.helpers.mcp_container_manager import McpContainerManager

        mock_docker.containers.list.return_value = []
        mgr = McpContainerManager()
        status = mgr.get_status("nonexistent")
        assert status["running"] is False
        assert status["container_id"] is None
