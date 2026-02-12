# MCP Server OAuth Authentication

This guide explains how to secure inbound MCP connections with Microsoft Entra ID OAuth, allowing IDE clients (VS Code, Cursor, Claude Code) to authenticate with Bearer tokens.

## Overview

Apollos AI exposes an MCP server at `/mcp` that IDE clients can connect to. By default, access is controlled via a shared **token-in-path** mechanism (the MCP server token from Settings). Phase 5 adds optional **OAuth Bearer token** authentication via Entra ID, enabling per-user identity and RBAC enforcement for MCP requests.

Both authentication methods coexist — enabling OAuth does not break token-in-path access.

## Prerequisites

- Apollos AI with Phase 5 auth system (Phases 0–4 complete)
- A Microsoft Entra ID tenant
- Azure Portal admin access to create App Registrations

## Azure App Registration

Create a **separate** App Registration for the MCP server (don't reuse the OIDC SSO app).

### 1. Register the app

1. Go to **Azure Portal** > **App registrations** > **New registration**
2. Name: `Apollos AI MCP API` (or similar)
3. Supported account types: Choose based on your needs
   - **Single tenant** for internal use
   - **Multitenant** if external clients need access
4. Redirect URI: Leave blank for now (clients provide their own)
5. Click **Register**

### 2. Expose an API

1. Go to **Expose an API**
2. Set **Application ID URI**: Accept the default (`api://{client-id}`) or set a custom one
3. **Add scopes** (these must match the server config):
   - `discover` — List available tools
   - `tools.read` — Read tool metadata
   - `tools.execute` — Execute tools
   - `chat` — Send and manage chat messages

### 3. Create a client secret

1. Go to **Certificates & secrets** > **New client secret**
2. Copy the secret value immediately (it won't be shown again)

### 4. Authorize client apps

For each IDE client app that will connect:

1. Go to **Expose an API** > **Add a client application**
2. Enter the client's Application ID
3. Check all four scopes

## Server Configuration

Add these environment variables to `usr/.env`:

```bash
# Required — enables MCP OAuth
MCP_AZURE_CLIENT_ID=<app-registration-client-id>
MCP_AZURE_CLIENT_SECRET=<client-secret-value>
MCP_AZURE_TENANT_ID=<your-tenant-guid>

# Required for production
MCP_SERVER_BASE_URL=https://your-domain.com
MCP_AZURE_JWT_SIGNING_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

# Optional
# MCP_AZURE_IDENTIFIER_URI=api://<client-id>
# MCP_AZURE_REDIRECT_URIS=http://localhost:50080/callback
```

Restart the server. You should see:

```text
[MCP] Azure OAuth auth configured via AzureProvider
```

## How It Works

### Dual authentication

| Method | Endpoint | Use case |
|--------|----------|----------|
| Token-in-path | `/mcp/t-{token}/http` | Simple API access, legacy clients |
| OAuth Bearer | `/mcp/http` | IDE clients, per-user identity |

### OAuth flow

1. Client connects to `/mcp/http`
2. Server returns 401 with Protected Resource Metadata (PRM)
3. Client initiates OAuth authorization code flow with Entra ID
4. User authenticates in browser
5. Client receives access token with granted scopes
6. Client sends requests with `Authorization: Bearer {token}`
7. Server validates JWT via JWKS, enforces scopes, resolves user identity

### Per-tool scope enforcement

Tools require the `chat` scope. Without it, tools are hidden from `tools/list`:

```text
send_message  → requires "chat" scope
finish_chat   → requires "chat" scope
```

### RBAC enforcement

If the authenticated user exists in the auth database, Casbin RBAC is checked to verify MCP execute permissions within the user's org/team domain.

## IDE Client Configuration

### Claude Code

In Claude Code settings, add an MCP server:

```json
{
  "mcpServers": {
    "apollos-ai": {
      "url": "https://your-domain.com/mcp/http",
      "auth": "oauth"
    }
  }
}
```

### VS Code (Copilot MCP)

In VS Code settings:

```json
{
  "mcp.servers": {
    "apollos-ai": {
      "url": "https://your-domain.com/mcp/http",
      "auth": "oauth"
    }
  }
}
```

## Security Features

### Rate limiting

OAuth-authenticated MCP requests are rate-limited to 100 requests/minute per user.

### Audit logging

All MCP tool invocations are logged to the `audit_log` table with:
- User ID (from token claims)
- Action (`mcp_tool_invoke`)
- Resource (tool name)
- Details (chat ID, project)

### Login brute force protection

Local login attempts are protected with:
- Progressive delays (0, 1, 2, 4, 8 seconds)
- Account lockout after 5 failed attempts (5-minute cooldown)

## Troubleshooting

### "MCP forbidden" error

- Verify MCP server is enabled in Settings
- Check that the token-in-path is correct (for token-in-path mode)
- Verify OAuth env vars are set (for Bearer mode)

### OAuth flow not starting

- Verify `MCP_AZURE_CLIENT_ID`, `MCP_AZURE_CLIENT_SECRET`, `MCP_AZURE_TENANT_ID` are all set
- Check that `MCP_SERVER_BASE_URL` matches your actual server URL
- Verify the Azure App Registration has the correct scopes exposed

### Token rejected

- Verify the tenant ID is a specific GUID (not "common")
- Check that the client app is authorized in "Expose an API"
- Verify the user exists in the auth database (for RBAC)
