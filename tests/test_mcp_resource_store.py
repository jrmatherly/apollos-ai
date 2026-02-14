"""Tests for MCP resource store abstraction."""


class TestInMemoryMcpResourceStore:
    def test_get_returns_none_for_missing(self):
        from python.helpers.mcp_resource_store import InMemoryMcpResourceStore

        store = InMemoryMcpResourceStore()
        assert store.get("nonexistent") is None

    def test_upsert_and_get(self):
        from python.helpers.mcp_resource_store import (
            InMemoryMcpResourceStore,
            McpServerResource,
        )

        store = InMemoryMcpResourceStore()
        resource = McpServerResource(
            name="github",
            transport_type="streamable_http",
            url="http://mcp-github:8000/mcp",
            created_by="admin",
        )
        store.upsert(resource)
        result = store.get("github")
        assert result is not None
        assert result.name == "github"
        assert result.url == "http://mcp-github:8000/mcp"

    def test_upsert_overwrites(self):
        from python.helpers.mcp_resource_store import (
            InMemoryMcpResourceStore,
            McpServerResource,
        )

        store = InMemoryMcpResourceStore()
        r1 = McpServerResource(name="gh", transport_type="stdio", created_by="admin")
        r2 = McpServerResource(
            name="gh",
            transport_type="streamable_http",
            url="http://new:8000",
            created_by="admin",
        )
        store.upsert(r1)
        store.upsert(r2)
        result = store.get("gh")
        assert result.transport_type == "streamable_http"

    def test_delete(self):
        from python.helpers.mcp_resource_store import (
            InMemoryMcpResourceStore,
            McpServerResource,
        )

        store = InMemoryMcpResourceStore()
        store.upsert(
            McpServerResource(name="x", transport_type="stdio", created_by="admin")
        )
        store.delete("x")
        assert store.get("x") is None

    def test_list_all(self):
        from python.helpers.mcp_resource_store import (
            InMemoryMcpResourceStore,
            McpServerResource,
        )

        store = InMemoryMcpResourceStore()
        store.upsert(
            McpServerResource(name="a", transport_type="stdio", created_by="admin")
        )
        store.upsert(
            McpServerResource(name="b", transport_type="stdio", created_by="admin")
        )
        assert len(store.list_all()) == 2

    def test_list_all_empty(self):
        from python.helpers.mcp_resource_store import InMemoryMcpResourceStore

        store = InMemoryMcpResourceStore()
        assert store.list_all() == []


class TestMcpServerResourcePermissions:
    """Test the creator + role-based permission model (from MS MCP Gateway)."""

    def test_creator_has_read_access(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(name="x", transport_type="stdio", created_by="user1")
        assert r.can_access("user1", roles=[], operation="read")

    def test_creator_has_write_access(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(name="x", transport_type="stdio", created_by="user1")
        assert r.can_access("user1", roles=[], operation="write")

    def test_admin_has_write_access(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(
            name="x", transport_type="stdio", created_by="someone_else"
        )
        assert r.can_access("admin", roles=["mcp.admin"], operation="write")

    def test_matching_role_has_read_access(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(
            name="x",
            transport_type="stdio",
            created_by="someone",
            required_roles=["engineering"],
        )
        assert r.can_access("user2", roles=["engineering"], operation="read")

    def test_non_matching_role_denied_read(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(
            name="x",
            transport_type="stdio",
            created_by="someone",
            required_roles=["engineering"],
        )
        assert not r.can_access("user2", roles=["sales"], operation="read")

    def test_non_creator_denied_write(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(name="x", transport_type="stdio", created_by="someone")
        assert not r.can_access("user2", roles=["engineering"], operation="write")

    def test_no_required_roles_allows_read(self):
        from python.helpers.mcp_resource_store import McpServerResource

        r = McpServerResource(
            name="x", transport_type="stdio", created_by="someone", required_roles=[]
        )
        assert r.can_access("anyone", roles=[], operation="read")
