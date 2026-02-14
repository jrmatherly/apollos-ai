"""Tests for MCP identity header injection and stripping."""


class TestBuildIdentityHeaders:
    def test_builds_headers_from_user_dict(self):
        from python.helpers.mcp_identity import build_identity_headers

        user = {"id": "user-123", "name": "Jason", "roles": ["member", "engineering"]}
        headers = build_identity_headers(user)
        assert headers["X-Mcp-UserId"] == "user-123"
        assert headers["X-Mcp-UserName"] == "Jason"
        assert headers["X-Mcp-Roles"] == "member,engineering"

    def test_handles_empty_roles(self):
        from python.helpers.mcp_identity import build_identity_headers

        user = {"id": "u1", "name": "Test", "roles": []}
        headers = build_identity_headers(user)
        assert headers["X-Mcp-Roles"] == ""

    def test_handles_missing_name(self):
        from python.helpers.mcp_identity import build_identity_headers

        user = {"id": "u1", "roles": ["viewer"]}
        headers = build_identity_headers(user)
        assert headers["X-Mcp-UserName"] == ""


class TestStripAuthHeaders:
    def test_strips_authorization(self):
        from python.helpers.mcp_identity import strip_auth_headers

        headers = {
            "Authorization": "Bearer token123",
            "Content-Type": "application/json",
            "Cookie": "session=abc",
        }
        cleaned = strip_auth_headers(headers)
        assert "Authorization" not in cleaned
        assert "Cookie" not in cleaned
        assert cleaned["Content-Type"] == "application/json"

    def test_preserves_non_auth_headers(self):
        from python.helpers.mcp_identity import strip_auth_headers

        headers = {"X-Custom": "value", "Accept": "application/json"}
        cleaned = strip_auth_headers(headers)
        assert cleaned == headers


class TestPrepareProxyHeaders:
    def test_combines_strip_and_inject(self):
        from python.helpers.mcp_identity import prepare_proxy_headers

        original = {"Authorization": "Bearer secret", "Accept": "text/plain"}
        user = {"id": "u1", "name": "Test", "roles": ["member"]}
        result = prepare_proxy_headers(original, user)
        assert "Authorization" not in result
        assert result["X-Mcp-UserId"] == "u1"
        assert result["Accept"] == "text/plain"
