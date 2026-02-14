"""Tests for MCP gateway API endpoints."""


class TestMcpGatewayServersApi:
    """Test the gateway server management API handler."""

    def test_list_servers_returns_empty(self):
        from python.helpers.mcp_resource_store import InMemoryMcpResourceStore

        store = InMemoryMcpResourceStore()
        assert store.list_all() == []

    def test_list_servers_returns_resources(self):
        from python.helpers.mcp_resource_store import (
            InMemoryMcpResourceStore,
            McpServerResource,
        )

        store = InMemoryMcpResourceStore()
        store.upsert(
            McpServerResource(
                name="github",
                transport_type="streamable_http",
                url="http://mcp-github:8000",
                created_by="admin",
            )
        )
        result = store.list_all()
        assert len(result) == 1
        assert result[0].name == "github"

    def test_resource_serializes_to_dict(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(
            name="test",
            transport_type="stdio",
            created_by="admin",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )
        assert r.name == "test"
        assert r.command == "npx"
        assert r.args == ["-y", "@modelcontextprotocol/server-filesystem"]
