# Project Index: Apollos AI

Generated: 2026-02-14

## Project Overview

Personal organic agentic AI framework that grows and learns with the user.
Fork of [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero), maintained at [jrmatherly/apollos-ai](https://github.com/jrmatherly/apollos-ai).

- **Language**: Python 3.12+ (backend), vanilla JS + Alpine.js (frontend)
- **Server**: Flask + uvicorn + python-socketio (ASGI)
- **LLM**: LiteLLM multi-provider (via LangChain wrappers)
- **Memory**: FAISS vector DB + sentence-transformers embeddings
- **Auth**: OIDC (Entra ID) + local Argon2id + RBAC (Casbin)
- **License**: MIT

## Project Structure

```text
apollos-ai/
├── agent.py              # Core Agent class (monologue loop)
├── models.py             # LiteLLM multi-provider model config
├── initialize.py         # Agent initialization from settings
├── run_ui.py             # Main entry point (Flask+uvicorn+socketio)
├── preload.py            # Pre-initialization routines
├── prepare.py            # Environment preparation
├── run_tunnel.py         # Cloudflare tunnel management
├── pyproject.toml        # Dependencies & project config (uv)
├── uv.lock               # Reproducible dependency lockfile
├── mise.toml             # Task runner + tool manager (93 tasks)
├── hk.pkl                # Git hooks config (pre-commit, commit-msg)
├── cliff.toml            # Changelog generation (conventional commits)
├── biome.json            # CSS/JS linter config
├── alembic.ini           # Database migration config
├── .drift/               # DriftDetect codebase analysis artifacts
│   ├── config.json       # Drift project config
│   ├── manifest.json     # Analysis manifest
│   ├── patterns/approved/# 14 approved pattern categories
│   ├── indexes/          # Category + file indexes
│   ├── views/            # Status cache + pattern index
│   ├── audit/            # Quality audit snapshots
│   ├── dna/              # Codebase DNA profiles
│   └── error-handling/   # Error topology analysis
├── .github/workflows/    # CI/CD (9 workflows)
├── python/
│   ├── api/              # 85 REST endpoint handlers (ApiHandler)
│   ├── tools/            # 19 active tools (Tool subclasses)
│   ├── helpers/          # 103 utility modules
│   ├── extensions/       # 41 lifecycle hook extensions (24 hook dirs)
│   └── websocket_handlers/  # 4 namespace-based WS handlers
├── prompts/              # 102 prompt templates (99 .md + 3 .py)
├── webui/                # Frontend (Alpine.js + Socket.IO)
│   ├── components/       # 100 HTML component templates
│   ├── js/               # 21 JS modules
│   ├── css/              # 11 stylesheets
│   └── vendor/           # Ace editor, Alpine.js, Socket.IO, etc.
├── agents/               # 6 agent profiles (default, apollos, developer, hacker, researcher, _example)
├── skills/               # Skill definitions (create-skill template)
├── knowledge/            # Knowledge base (main + solutions)
├── tests/                # 49 test files (pytest + pytest-asyncio)
├── docker/               # Docker build (base + run stages)
├── docs/                 # Documentation (setup, guides, developer, reference)
├── conf/                 # Runtime config (model_providers, rbac_model, gitignores)
├── alembic/              # Database migrations (SQLAlchemy + Alembic)
├── CLAUDE.md             # AI agent guidance
├── QUICKSTART.md         # Quickstart guide
└── STYLING-PLAYBOOK.md   # Drift DNA-generated styling guide
```

## Entry Points

- **UI Server**: `run_ui.py` — Flask + uvicorn + Socket.IO ASGI app
- **Tunnel**: `run_tunnel.py` — Cloudflare tunnel for remote access
- **Agent Core**: `agent.py` — Agent class with monologue loop
- **Init**: `initialize.py` — Agent config assembly from settings
- **Models**: `models.py` — LiteLLM model configuration (chat, utility, embedding, browser)

## Core Modules

### agent.py — Agent & AgentContext
- `Agent`: Monologue loop (prompt → LLM → parse JSON → tool exec → repeat)
- `AgentContext`: Thread-safe session lifecycle with locking
- Loop terminates when `response` tool is called

### models.py — Model Configuration
- `ModelConfig`: Dataclass for LiteLLM provider settings
- `ChatGenerationResult`: Streaming response processor
- Supports: chat, utility, embedding, browser model types

### initialize.py — Agent Initialization
- Builds agent config from UI settings
- Assembles model configs, runs migrations, initializes MCP

### run_ui.py — Server
- Flask app with ASGI (a2wsgi) + uvicorn
- Auto-discovers API handlers from `python/api/`
- Socket.IO namespace routing via `websocket_namespace_discovery`
- Auth: session + API key + CSRF + loopback-only modes + OIDC + RBAC
- Mounts: MCP server (`/mcp`), A2A server (`/.well-known/agent.json`)

## Tools (19 active)

| Tool | Purpose |
|------|---------|
| `code_execution_tool` | Execute code (Python, Node.js, terminal) in Docker sandbox |
| `call_subordinate` | Spawn sub-agents for delegated tasks |
| `response` | Return final response to user (ends loop) |
| `memory_save` | Save to FAISS vector memory |
| `memory_load` | Query FAISS vector memory |
| `memory_delete` | Delete specific memories |
| `memory_forget` | Bulk forget by criteria |
| `search_engine` | Web search (SearXNG/DuckDuckGo/Perplexity) |
| `browser_agent` | Browser automation (Playwright/browser-use) |
| `document_query` | Query uploaded documents |
| `input` | Request user input mid-task |
| `notify_user` | Send push/email notifications |
| `scheduler` | Cron-based task scheduling |
| `skills_tool` | Execute installed skills |
| `a2a_chat` | Agent-to-agent communication |
| `behaviour_adjustment` | Modify agent behavior dynamically |
| `vision_load` | Load images for vision analysis |
| `wait` | Pause execution |
| `unknown` | Fallback for unrecognized tool calls |

## API Handlers (85 endpoints)

Key endpoint groups:

- **Chat**: `message`, `message_async`, `chat_create`, `chat_load`, `chat_reset`, `chat_remove`, `chat_export`, `chat_files_path_get`
- **Settings**: `settings_get`, `settings_set`, `settings_workdir_file_structure`
- **Memory**: `memory_dashboard`
- **Files**: `get_work_dir_files`, `upload_work_dir_files`, `edit_work_dir_file`, `delete_work_dir_file`, `download_work_dir_file`, `rename_work_dir_file`, `file_info`
- **MCP**: `mcp_servers_status`, `mcp_servers_apply`, `mcp_server_get_detail`, `mcp_server_get_log`, `mcp_connections`, `mcp_oauth_start`, `mcp_services`
- **Admin**: `admin_users`, `admin_api_keys`, `admin_group_mappings`, `admin_orgs`, `admin_teams`
- **Scheduler**: `scheduler_tasks_list`, `scheduler_task_create`, `scheduler_task_update`, `scheduler_task_delete`, `scheduler_task_run`, `scheduler_tick`
- **Backup**: `backup_create`, `backup_restore`, `backup_inspect`, `backup_test`, `backup_preview_grouped`, `backup_restore_preview`, `backup_get_defaults`
- **Knowledge**: `knowledge_reindex`, `knowledge_path_get`, `import_knowledge`
- **Skills**: `skills`, `skills_import`, `skills_import_preview`
- **Notifications**: `notification_create`, `notifications_history`, `notifications_mark_read`, `notifications_clear`
- **Auth**: `csrf_token`, `logout`, `user_profile`
- **System**: `health`, `poll`, `restart`, `nudge`, `pause`, `rfc`, `banners`, `agents`, `subagents`, `projects`, `switch_context`
- **Media**: `synthesize`, `transcribe`, `image_get`
- **Tunnel**: `tunnel`, `tunnel_proxy`
- **Upload**: `upload`, `upload_work_dir_files`
- **Context**: `ctx_window_get`, `history_get`
- **Queue**: `message_queue_add`, `message_queue_remove`, `message_queue_send`
- **Branding**: `branding_get`
- **API Compat**: `api_message`, `api_reset_chat`, `api_terminate_chat`, `api_files_get`, `api_log_get`

## Extension Lifecycle Hooks (24 directories, 41 extensions)

```text
agent_init (2) → message_loop_start (1) → message_loop_prompts_before (1) →
message_loop_prompts_after (6) → monologue_start (2) → system_prompt (2) →
before_main_llm_call (1) → reasoning_stream (1) → reasoning_stream_chunk (1) →
reasoning_stream_end (1) → response_stream (3) → response_stream_chunk (1) →
response_stream_end (2) → tool_execute_before (2) → tool_execute_after (1) →
hist_add_before (1) → hist_add_tool_result (1) → monologue_end (3) →
message_loop_end (2) → process_chain_end (1) → user_message_ui (1) →
banners (3) → error_format (1) → util_model_call_before (1)
```

Extensions sorted by filename prefix (`_10_`, `_20_`, etc.) within each hook.
User overrides: `usr/extensions/` (same filename = override).

### Extension Details

| Hook | Extensions |
|------|-----------|
| agent_init | `_10_initial_message`, `_15_load_profile_settings` |
| banners | `_10_unsecured_connection`, `_20_missing_api_key`, `_30_system_resources` |
| before_main_llm_call | `_10_log_for_stream` |
| error_format | `_10_mask_errors` |
| hist_add_before | `_10_mask_content` |
| hist_add_tool_result | `_90_save_tool_call_file` |
| message_loop_end | `_10_organize_history`, `_90_save_chat` |
| message_loop_prompts_after | `_50_recall_memories`, `_60_include_current_datetime`, `_65_include_loaded_skills`, `_70_include_agent_info`, `_75_include_workdir_extras`, `_91_recall_wait` |
| message_loop_prompts_before | `_90_organize_history_wait` |
| message_loop_start | `_10_iteration_no` |
| monologue_end | `_50_memorize_fragments`, `_51_memorize_solutions`, `_90_waiting_for_input_msg` |
| monologue_start | `_10_memory_init`, `_60_rename_chat` |
| process_chain_end | `_50_process_queue` |
| reasoning_stream | `_10_log_from_stream` |
| reasoning_stream_chunk | `_10_mask_stream` |
| reasoning_stream_end | `_10_mask_end` |
| response_stream | `_10_log_from_stream`, `_15_replace_include_alias`, `_20_live_response` |
| response_stream_chunk | `_10_mask_stream` |
| response_stream_end | `_10_mask_end`, `_15_log_from_stream_end` |
| system_prompt | `_10_system_prompt`, `_20_behaviour_prompt` |
| tool_execute_after | `_10_mask_secrets` |
| tool_execute_before | `_10_replace_last_tool_output`, `_10_unmask_secrets` |
| user_message_ui | `_10_update_check` |
| util_model_call_before | `_10_mask_secrets` |

## Helpers (103 modules)

### Authentication & Security
`auth.py`, `auth_bootstrap.py`, `auth_db.py`, `rbac.py`, `security.py`, `user_store.py`, `vault_crypto.py`, `crypto.py`, `secrets.py`, `login.py`, `login_protection.py`, `audit.py`

### Data & Storage
`backup.py`, `files.py`, `file_browser.py`, `file_tree.py`, `history.py`, `memory.py`, `memory_consolidation.py`, `multiuser_migration.py`, `persist_chat.py`, `vector_db.py`, `vector_store.py`, `state_snapshot.py`, `workspace.py`

### Agent System Core
`api.py`, `call_llm.py`, `context.py`, `defer.py`, `error_response.py`, `extension.py`, `extract_tools.py`, `job_loop.py`, `messages.py`, `projects.py`, `runtime.py`, `settings.py`, `subagents.py`, `tenant.py`, `tool.py`, `tokens.py`, `wait.py`

### Browser & Automation
`browser.py`, `browser_use.py`, `browser_use_monkeypatch.py`, `playwright.py`, `docker.py`, `process.py`

### Communication & I/O
`websocket.py`, `websocket_manager.py`, `websocket_namespace_discovery.py`, `notification.py`, `print_catch.py`, `print_style.py`, `timed_input.py`, `tty_session.py`, `tunnel_manager.py`, `email_client.py`, `fasta2a_client.py`, `fasta2a_server.py`

### Search & Knowledge
`document_query.py`, `duckduckgo_search.py`, `knowledge_import.py`, `perplexity_search.py`, `searxng.py`, `rfc.py`, `rfc_exchange.py`, `rfc_files.py`

### MCP Gateway
`mcp_handler.py`, `mcp_server.py`, `mcp_connection_pool.py`, `mcp_container_manager.py`, `mcp_identity.py`, `mcp_oauth.py`, `mcp_resource_store.py`

### Skills & Tasks
`skills.py`, `skills_cli.py`, `skills_import.py`, `task_scheduler.py`, `message_queue.py`

### Utilities
`attachment_manager.py`, `branding.py`, `dirty_json.py`, `dotenv.py`, `errors.py`, `faiss_monkey_patch.py`, `faiss_wrapper.py`, `git.py`, `guids.py`, `images.py`, `localization.py`, `log.py`, `migration.py`, `providers.py`, `rate_limiter.py`, `shell_local.py`, `shell_ssh.py`, `strings.py`, `update_check.py`

### State Management
`state_monitor.py`, `state_monitor_integration.py`, `state_snapshot.py`

### Media Processing
`kokoro_tts.py`, `whisper.py`

## WebSocket Handlers (4)

| Handler | Class |
|---------|-------|
| `_default.py` | `RootDefaultHandler` |
| `dev_websocket_test_handler.py` | `DevWebsocketTestHandler` |
| `hello_handler.py` | `HelloHandler` |
| `state_sync_handler.py` | `StateSyncHandler` |

## Authentication System (Phase 0–3)

### Phase 0: Foundation
- **Auth DB**: `auth_db.py` (SQLAlchemy engine), `user_store.py` (ORM + CRUD)
- **Migrations**: `alembic/` with `001_initial_schema.py`
- **Vault**: `vault_crypto.py` (AES-256-GCM, HKDF), env: `VAULT_MASTER_KEY`
- **Bootstrap**: `auth_bootstrap.py` — runs migrations + creates admin from `ADMIN_EMAIL`/`ADMIN_PASSWORD`

### Phase 1: OIDC + Local Login
- **OIDC**: `auth.py` (AuthManager, MSAL, PersistentTokenCache)
- **Env**: `OIDC_TENANT_ID`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_REDIRECT_URI`
- **Local login**: Argon2id password hashing, fallback from OIDC
- **Legacy compat**: `AUTH_LOGIN`/`AUTH_PASSWORD` still works
- **Session**: `session["user"] = {id, email, name, auth_method}`, `session["authentication"] = True`
- **Routes**: `/login` (GET/POST), `/login/entra`, `/auth/callback`, `/logout`

### Phase 2: User Isolation
- **Tenant context**: `tenant.py` (TenantContext) — multi-user data scoping
- **Migration**: `multiuser_migration.py` — data directory restructuring

### Phase 3: RBAC Authorization
- **RBAC model**: `conf/rbac_model.conf` (Casbin)
- **RBAC module**: `python/helpers/rbac.py`
- **Tests**: `tests/test_phase3_authorization.py`

## MCP Gateway

Built-in MCP gateway for routing, lifecycle, and access control:

- **Connection Pool**: `mcp_connection_pool.py` — persistent MCP sessions with health checking
- **Resource Store**: `mcp_resource_store.py` — pluggable backend (InMemory), creator+admin+role permissions
- **Identity Headers**: `mcp_identity.py` — X-Mcp-UserId/UserName/Roles injection, auth header stripping
- **Container Manager**: `mcp_container_manager.py` — Docker lifecycle for MCP server containers
- **OAuth**: `mcp_oauth.py` — MCP OAuth integration (Azure provider)
- **Proxy**: `DynamicMcpProxy` in `mcp_server.py` — ASGI reverse proxy at `/mcp`, routes SSE/HTTP/OAuth
- **Permission Model**: Resource-level RBAC per MCP server (creator + admin + required_roles)
- **Tests**: 5 test files (`test_mcp_connection_pool`, `test_mcp_container_manager`, `test_mcp_gateway_api`, `test_mcp_identity`, `test_mcp_resource_store`)

## Prompt Templates (102 files)

### Agent System Prompts (42)
- **Core**: `agent.system.main.md` and sub-templates (role, environment, communication, solving, tips)
- **Behavior**: `agent.system.behaviour.md`, `agent.system.behaviour_default.md`
- **Tools**: `agent.system.tools.md`, individual tool templates (`agent.system.tool.*.md`)
- **Features**: MCP, memories, projects, secrets, skills, solutions

### Framework Messages (43)
- **Responses**: `fw.ai_response.md`, `fw.initial_message.md`
- **Code execution**: info, max_time, no_output, pause, reset, running, runtime_wrong
- **Errors**: `fw.error.md`, `fw.warning.md`, `fw.msg_critical_error.md`, `fw.tool_not_found.md`
- **Memory**: saved, deleted, not_found, history summaries
- **Summarization**: bulk_summary, rename_chat, topic_summary

### Memory System (14)
- Consolidation, keyword extraction, filter, query, recall templates

### Behavior (4)
- Merge, search, updated templates

### Browser Agent (1)
- `browser_agent.system.md`

## Configuration

### Runtime Configuration (`conf/`)
- `model_providers.yaml` — LLM provider model definitions
- `rbac_model.conf` — RBAC authorization model (Casbin)
- `workdir.gitignore` — Working directory gitignore template
- `skill.default.gitignore` — Default skill .gitignore template
- `projects.default.gitignore` — Default project .gitignore template

### Root Configuration
- `pyproject.toml` — All Python dependencies + project metadata (managed by uv)
- `uv.lock` — Reproducible lockfile (committed)
- `requirements.txt` — Auto-generated by `uv export` for Docker compatibility
- `mise.toml` — Task runner (93 tasks) + tool management
- `hk.pkl` — Git hooks config (Pkl format)
- `cliff.toml` — Changelog generation (conventional commits)
- `biome.json` — Biome CSS/JS linter settings
- `alembic.ini` — Database migration config
- `jsconfig.json` — JS path config
- `.python-version` — Python version pinning (3.12)

## Branding System

- **Module**: `python/helpers/branding.py` — centralized config, reads env vars at import
- **Env vars**: `BRAND_NAME` (default "Apollos AI"), `BRAND_SLUG`, `BRAND_URL`, `BRAND_GITHUB_URL`, `BRAND_UPDATE_CHECK_URL`
- **API**: `/branding_get` endpoint returns JSON for frontend
- **Frontend**: `webui/js/branding-store.js` — Alpine.js store, consumed across all UI templates
- **Prompts**: `{{brand_name}}` variable injection in prompt templates
- **Update check**: GitHub Releases API (configurable, 1-hour cooldown)

## Docker Images

| Image | Dockerfile | Purpose |
|-------|-----------|---------|
| Base | `docker/base/Dockerfile` | Kali + system packages |
| App | `docker/run/Dockerfile` | Production image (FROM base, pulls from GitHub) |
| Local | `DockerfileLocal` | Development image (FROM base, uses working tree) |

Registry: `ghcr.io/jrmatherly/apollos-ai` (app), `ghcr.io/jrmatherly/apollos-ai-base` (base)

## Development Tooling

### mise (Task Runner + Tool Manager)
- `mise.toml` — 93 tasks, manages Python 3.12, uv, ruff, biome, git-cliff, pkl, hk
- Common: `mise run r` (UI), `mise run t` (tests), `mise run lint`, `mise run ci`
- Drift: 38 `drift:*` tasks (scan, patterns, memory, quality gates)
- Deps: `mise run deps:add <pkg>` (adds + regenerates requirements.txt)
- Docker: `mise run docker:build:base`, `docker:build:app`, `docker:build:local`, `docker:run`

### Git Hooks (hk)
- `hk.pkl` — Pre-commit: Ruff lint, Biome CSS, security checks, hygiene
- Commit-msg: Conventional commit format enforcement

### Changelog (git-cliff)
- `cliff.toml` — Conventional commit parsing, Keep a Changelog format
- `mise run changelog` / `mise run changelog:latest`

### DriftDetect (Codebase Analysis)
- `.drift/` — Pattern scanning, Python analysis, Cortex memory, quality gates
- Installed via npm (`driftdetect@0.9.48`), supports Python via tree-sitter
- Key: `mise run drift:scan`, `drift:py`, `drift:memory`, `drift:check`, `drift:gate`

## CI/CD (9 GitHub Actions Workflows)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to main | Lint (Ruff + Biome) + format check + test (parallel) |
| `claude.yml` | Issue/PR comments, assigned issues | Claude Code agent for automated responses |
| `claude-code-review.yml` | PR open/sync/ready | Claude Code automated PR review |
| `release.yml` | `v*` tag push | git-cliff changelog + GitHub release + Docker app image |
| `docker-base.yml` | `docker/base/**` changes | Build + push Docker base image to GHCR |
| `drift.yml` | Manual dispatch | DriftDetect codebase analysis (disabled) |
| `hooks-check.yml` | PRs to main | hk hook validation |
| `codeql.yml` | Push/PR to main + weekly | CodeQL security analysis (Python) |
| `dependency-review.yml` | PRs | Dependency vulnerability + requirements.txt sync |

Additional: Dependabot (weekly uv + GitHub Actions + Docker updates), issue templates (YAML forms), PR template.

## Tests (49 files)

### Authentication & Security (14)
- `test_auth_phase0.py` — Phase 0 foundation (26 tests)
- `test_auth_phase1.py` — Phase 1 OIDC + local login (37 tests)
- `test_phase2_user_isolation.py` — Phase 2 tenant isolation
- `test_phase3_authorization.py` — Phase 3 RBAC (24 tests)
- `test_phase4a_admin.py` — Phase 4 admin endpoints
- `test_phase4b_mcp_client.py` — Phase 4 MCP client auth
- `test_phase5_audit.py` — Phase 5 audit logging
- `test_phase5_cross_tenant.py` — Phase 5 cross-tenant isolation
- `test_phase5_login_protection.py` — Phase 5 brute force protection
- `test_phase5_mcp_auth.py` — Phase 5 MCP authentication
- `test_security.py` — General security
- `test_security_boundaries.py` — Security boundary validation
- `test_http_auth_csrf.py` — HTTP auth + CSRF
- `test_websocket_csrf.py` — WebSocket CSRF

### WebSocket (14)
- `test_websocket_manager.py`, `test_websocket_handlers.py`, `test_websocket_namespaces.py`
- `test_websocket_namespaces_integration.py`, `test_websocket_namespace_discovery.py`
- `test_websocket_namespace_security.py`, `test_websocket_root_namespace.py`
- `test_websocket_client_api_surface.py`, `test_websocket_harness.py`
- `test_socketio_library_semantics.py`, `test_socketio_unknown_namespace.py`
- `test_state_sync_handler.py`, `test_state_sync_welcome_screen.py`
- `websocket_namespace_test_utils.py` (shared utilities)

### MCP Gateway (5)
- `test_mcp_connection_pool.py` — Connection pool management
- `test_mcp_container_manager.py` — Docker container lifecycle
- `test_mcp_gateway_api.py` — Gateway API integration
- `test_mcp_identity.py` — Identity header injection
- `test_mcp_resource_store.py` — Resource store permissions

### Features (7)
- `test_branding.py` — Branding system
- `test_multi_tab_isolation.py` — Multi-tab state isolation
- `test_state_monitor.py` — State monitoring
- `test_snapshot_parity.py`, `test_snapshot_schema_v1.py` — State snapshots
- `test_persist_chat_log_ids.py` — Chat persistence
- `test_settings_developer_sections.py` — Settings sections

### Agent Core (1)
- `test_agent_core.py` — Core agent functionality

### Configuration (1)
- `test_run_ui_config.py` — Server configuration

### Utilities (5)
- `chunk_parser_test.py`, `email_parser_test.py` (manual)
- `test_fasta2a_client.py`, `test_file_tree_visualize.py`
- `test_file_browser_isolation.py` — File browser isolation

### Manual / Performance (1)
- `rate_limiter_manual.py`

### Shared
- `conftest.py` — Shared test fixtures

Run: `mise run t`

## Documentation

### Setup
- `docs/setup/installation.md` — Full installation
- `docs/setup/dev-setup.md` — Developer environment
- `docs/setup/vps-deployment.md` — VPS deployment
- `docs/setup/dependency-management.md` — uv + pyproject.toml workflow

### Guides
- `docs/guides/usage.md` — Usage guide
- `docs/guides/projects.md` — Projects feature
- `docs/guides/mcp-setup.md` — MCP setup
- `docs/guides/mcp-server-auth.md` — MCP server authentication (OAuth, tokens)
- `docs/guides/a2a-setup.md` — Agent-to-Agent setup
- `docs/guides/api-integration.md` — API integration
- `docs/guides/azure-enterprise-setup.md` — Azure Entra ID SSO configuration
- `docs/guides/production-deployment.md` — Production deployment guide
- `docs/guides/troubleshooting.md` — Troubleshooting
- `docs/guides/contribution.md` — Contributing

### Developer
- `docs/developer/architecture.md` — Architecture overview
- `docs/developer/extensions.md` — Extension system
- `docs/developer/websockets.md` — WebSocket documentation
- `docs/developer/mcp-configuration.md` — MCP server config
- `docs/developer/notifications.md` — Notification system
- `docs/developer/connectivity.md` — Connectivity
- `docs/developer/contributing-skills.md` — Skill development

### Reference
- `docs/reference/environment-variables.md` — Complete env var catalog

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `flask[async]` | 3.0.3 | Web framework |
| `uvicorn` | >=0.38.0 | ASGI server |
| `python-socketio` | >=5.14.2 | WebSocket support |
| `litellm` (via langchain) | — | Multi-provider LLM |
| `langchain-core` | 0.3.49 | LLM abstractions |
| `faiss-cpu` | 1.11.0 | Vector similarity search |
| `sentence-transformers` | 3.0.1 | Text embeddings |
| `fastmcp` | >=3.0.0rc2 | MCP server + gateway |
| `fasta2a` | 0.5.0 | Agent-to-Agent protocol |
| `browser-use` | 0.5.11 | Browser automation |
| `playwright` | 1.52.0 | Browser control |
| `docker` | 7.1.0 | Docker SDK |
| `pydantic` | 2.11.7 | Data validation |
| `duckduckgo-search` | 6.1.12 | Web search |
| `openai-whisper` | 20250625 | Speech-to-text |
| `kokoro` | >=0.9.2 | Text-to-speech |
| `sqlalchemy` | >=2.0 | Auth database ORM |
| `alembic` | — | Database migrations |
| `msal` | — | Microsoft Auth Library (OIDC) |
| `argon2-cffi` | — | Password hashing |
| `casbin` | — | RBAC authorization |

## Agent Profiles

| Profile | Description |
|---------|-------------|
| `default` | Base agent with standard capabilities |
| `apollos` | Core Apollos AI personality |
| `developer` | Software development focused |
| `hacker` | Security/hacking oriented |
| `researcher` | Research and analysis focused |
| `_example` | Template for custom profiles |

## Quick Start

1. `mise install` — Install all tools (Python, uv, ruff, biome, etc.)
2. `mise run setup` — First-time setup (deps, playwright, hooks)
3. `mise run r` — Start UI server (or `python run_ui.py`)
4. Configure API keys in UI settings
5. `mise run t` — Run tests (or `uv run pytest tests/`)

## Conventions

- Python: `snake_case` functions, `PascalCase` classes, `str | None` unions
- Tools: extend `Tool`, implement `async execute(**kwargs) -> Response`
- API: extend `ApiHandler`, implement `async process(input, request) -> dict`
- Extensions: extend `Extension`, implement `async execute(**kwargs)`, prefix-sorted
- Disabled files: `._py` suffix
- Prompt templates: `{{ include }}` and `{{variable}}` syntax
- Commits: Conventional Commits format (enforced by hk commit-msg hook)
- GitHub remote: `jrmatherly/apollos-ai` (fork of `agent0ai/agent-zero`)

## File Counts Summary

| Component | Count |
|-----------|-------|
| API handlers | 85 |
| Tools (active) | 19 |
| Helper modules | 103 |
| Extension files | 41 (in 24 hook directories) |
| WebSocket handlers | 4 |
| Prompt templates | 102 (99 .md + 3 .py) |
| Frontend components | 100 HTML |
| Frontend JS modules | 21 |
| Frontend CSS modules | 11 |
| Test files | 49 |
| CI/CD workflows | 9 |
| Agent profiles | 6 |
| Configuration files (conf/) | 5 |
| Root config files | 10 |
| Documentation files | 24 |
