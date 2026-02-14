"""MCP identity header utilities.

Implements the X-Mcp-* identity header pattern from Microsoft MCP Gateway:
- Strip inbound auth headers (Authorization, Cookie) before proxying
- Inject sanitized identity headers for downstream MCP servers
"""

from __future__ import annotations

# Headers to strip when proxying to MCP servers
_AUTH_HEADERS = frozenset({"authorization", "cookie", "x-csrf-token"})


def build_identity_headers(user: dict) -> dict[str, str]:
    """Build X-Mcp-* identity headers from a user dict.

    Args:
        user: Dict with keys ``id``, ``name`` (optional), ``roles`` (list).

    Returns:
        Dict of identity headers to inject into proxied requests.
    """
    roles = user.get("roles", [])
    return {
        "X-Mcp-UserId": str(user.get("id", "")),
        "X-Mcp-UserName": str(user.get("name", "")),
        "X-Mcp-Roles": ",".join(str(r) for r in roles),
    }


def strip_auth_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove authentication headers before forwarding to MCP servers.

    Strips Authorization, Cookie, and CSRF tokens so downstream MCP
    servers never see the user's raw credentials.
    """
    return {k: v for k, v in headers.items() if k.lower() not in _AUTH_HEADERS}


def prepare_proxy_headers(
    original_headers: dict[str, str], user: dict
) -> dict[str, str]:
    """Strip auth headers and inject MCP identity headers.

    Convenience function combining :func:`strip_auth_headers` and
    :func:`build_identity_headers`.
    """
    cleaned = strip_auth_headers(original_headers)
    cleaned.update(build_identity_headers(user))
    return cleaned
