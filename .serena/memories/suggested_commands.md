# Suggested Commands

## mise Task Runner (Primary Interface)

mise manages all tools and tasks. Run `mise task ls` to see all 67 tasks.

```bash
# Common shortcuts
mise run r              # Start UI server (run_ui.py)
mise run t              # Run tests (pytest)
mise run lint           # Lint all (Python + CSS)
mise run format         # Format all code
mise run format:check   # Format check (CI-friendly, no writes)
mise run ci             # Run all CI checks (lint, format, test)
mise run setup          # First-time setup (deps, playwright, hooks)
mise run install        # Install Python dependencies (uv sync)
mise run info           # Show tool versions and environment info
```

## Linting & Formatting
```bash
mise run lint:python       # Lint Python with Ruff
mise run lint:css          # Lint CSS with Biome
mise run lint:python:fix   # Auto-fix Python lint issues
mise run format:python     # Format Python with Ruff
mise run format:check      # Check formatting (no writes)
```

## Testing
```bash
mise run test              # Run all tests
mise run test:coverage     # Run tests with coverage report
uv run pytest tests/ -v    # Direct pytest invocation
uv run pytest tests/test_websocket_manager.py  # Single test file
```

## Git Hooks (hk)
```bash
mise run hooks:install     # Install git hooks via hk
mise run hooks:check       # Run all hook checks manually
mise run hooks:fix         # Run all hook fixes
```

## Changelog (git-cliff)
```bash
mise run changelog         # Generate full changelog
mise run changelog:latest  # Show latest version changelog
mise run changelog:bump    # Bump version based on conventional commits
```

## DriftDetect (Codebase Analysis)
```bash
mise run drift:scan           # Full codebase pattern scan
mise run drift:scan:incremental # Incremental scan (changed files only)
mise run drift:status         # Quick codebase health overview
mise run drift:py             # Python project analysis
mise run drift:py:routes      # List all HTTP routes
mise run drift:py:errors      # Analyze error handling patterns
mise run drift:py:async       # Analyze async patterns
mise run drift:patterns       # List all discovered patterns
mise run drift:check          # Check for pattern violations
mise run drift:gate           # Run quality gates
mise run drift:memory         # Cortex memory status
mise run drift:audit          # Audit for duplicates and issues
mise run drift:build          # Build all infrastructure (callgraph, coupling)
```

## Dependency Management (uv)
```bash
mise run deps:add <pkg>    # Add dependency + regenerate requirements.txt
uv add <pkg>               # Add to pyproject.toml
uv lock                    # Regenerate lockfile
uv export --no-hashes --no-dev --no-emit-project -o requirements.txt
```

## Docker
```bash
mise run docker:build:local         # Build local dev image from working tree
mise run docker:build:base          # Build base image (Kali + system packages)
mise run docker:build:app           # Build app image from main branch
mise run docker:build:app testing   # Build app image from a specific branch
mise run docker:build               # Build base + local in order
mise run docker:push:base           # Build + push base image to GHCR
mise run docker:push:app            # Build + push app image to GHCR
mise run docker:run                 # Run local container (port 50080→80)
```

## Environment
- Configuration via `usr/.env` file and `A0_SET_` environment variables (see `usr/.env.example` for template)
- Full variable catalog: `docs/reference/environment-variables.md`
- Settings managed through `python/helpers/settings.py`
- Web UI available at http://localhost:50001 (Docker) or configured port
