# Docker Infrastructure

## Three Docker Images

| Image | Dockerfile | Build Context | Purpose |
|-------|-----------|---------------|---------|
| **Base** (`apollos-ai-base`) | `docker/base/Dockerfile` | `docker/base/` | Kali Linux + system packages, Python, SearXNG, SSH |
| **App** (`apollos-ai`) | `docker/run/Dockerfile` | `docker/run/` | Clones repo from git branch, installs A0 on top of base |
| **Local** (`apollos-ai-local`) | `DockerfileLocal` | `.` (project root) | Copies local working tree into base image |

## Dependency Chain
- Base image: `FROM kalilinux/kali-rolling`
- App and Local both: `FROM ghcr.io/jrmatherly/apollos-ai-base:latest`
- Base must be built/available before app or local can build

## mise Tasks (mise.toml)

```
docker:build:base           Build base image locally
docker:build:app [branch]   Build app image from git branch (default: main)
docker:build:local          Build local dev image from working tree
docker:build                Build base + local in order (depends on both)
docker:push:base            Build + push base to GHCR (amd64)
docker:push:app [branch]    Build + push app to GHCR (amd64)
docker:run                  Run local container (port 50080→80)
```

## CI/CD Workflows
- `release.yml`: Builds + pushes app image on `v*` tag push (amd64 only)
- `docker-base.yml`: Builds + pushes base image on `docker/base/**` changes or manual dispatch

## GHCR Registry
- App: `ghcr.io/jrmatherly/apollos-ai` (tags: latest, v*.*.*, development, testing)
- Base: `ghcr.io/jrmatherly/apollos-ai-base` (tag: latest)

## Key Build Details

### Shell Compatibility
- Base image: `/bin/sh → dash` (NOT bash)
- All scripts sourced from Dockerfile `RUN` instructions run under `/bin/sh -c`
- Scripts must use POSIX `.` (dot) instead of `source` (bash-ism) when sourced from Dockerfiles
- Scripts invoked with `bash /path/to/script.sh` can use bash features
- `setup_venv.sh` is sourced (not executed) — must remain POSIX-compatible

### Layer Caching (DockerfileLocal)
- `requirements.txt` + `overrides.txt` copied first as a separate layer
- Python packages install in a cached layer — only rebuilds when deps change
- Source code copied after deps → source changes don't re-download packages
- Build with cached layers: ~1-2s; full rebuild: ~200s

### CMD Pattern
- Both Dockerfiles use: `CMD ["sh", "-c", "exec /exe/initialize.sh $BRANCH"]`
- JSON exec form for proper BuildKit compliance
- `sh -c` enables `$BRANCH` environment variable expansion
- `exec` ensures proper PID 1 signal handling → supervisord receives SIGTERM directly

### Dead Scripts Removed
- `install_additional.sh` — was entirely commented out, no longer referenced

## Supervisord Configuration

File: `docker/run/fs/etc/supervisor/conf.d/supervisord.conf`

### Logging
- `logfile=/dev/null` + `loglevel=warn` — eliminates duplicate supervisord meta-messages from container logs
- Each `[program:*]` section has `stdout_logfile=/dev/stdout` for program output
- Only warnings/errors from supervisord itself appear; program output is unaffected

### Rich Console Width (fastmcp)
- `[program:run_ui]` has `environment=COLUMNS="200",LINES="50"`
- Prevents Rich library (used by fastmcp) from word-wrapping at 80 columns in Docker
- Rich checks `COLUMNS` env var before `os.get_terminal_size()` fallback

### Structured Startup Output
- PrintStyle class (`python/helpers/print_style.py`) provides `banner()`, `phase()`, `step()`, `ready()` methods
- Startup sequence uses emoji-annotated phases with tree-style indented steps
- Shell scripts use emoji prefixes for container-level messages

## Build References
- `docker/base/build.txt` — Manual build commands for base image (local + GHCR + multi-arch)
- `docker/run/build.txt` — Manual build commands for app image (local + GHCR + multi-arch)
- `docs/setup/dev-setup.md` — Developer documentation for all Docker workflows
