# Stacks - Anna's Archive Download Manager

## Overview

Stacks is a containerized download queue manager for Anna's Archive. It provides
a web dashboard, Tampermonkey browser integration, and a REST API for managing
book downloads with fast download support and mirror fallbacks.

## Environment Variables

The following environment variables configure agent access to the Stacks API:

- **`STACKS_URL`** — Base URL of the Stacks server (default: `http://localhost:7788`)
- **`STACKS_API_KEY`** — Admin API key for full access, or Downloader API key for queue-only access

These must be set for the `/librarian` command to work. Get your API key from
the Stacks web UI: Settings → Authentication → API Key.

## Stacks REST API Reference

All authenticated endpoints require the header: `X-API-Key: <key>`

### Queue a Download

```bash
curl -X POST "${STACKS_URL}/api/queue/add" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${STACKS_API_KEY}" \
  -d '{"md5": "<md5_hash>", "source": "librarian-agent", "subfolder": "<optional>"}'
```

The `md5` field accepts a 32-character MD5 hash. Anna's Archive URLs containing
an MD5 are also accepted — the server extracts the hash automatically.

### Check Status

```bash
curl -s "${STACKS_URL}/api/status" -H "X-API-Key: ${STACKS_API_KEY}"
```

Returns current download, queue contents, download history, and fast download
remaining quota.

### List Subdirectories

```bash
curl -s "${STACKS_URL}/api/subdirs" -H "X-API-Key: ${STACKS_API_KEY}"
```

### Health Check (no auth required)

```bash
curl -s "${STACKS_URL}/api/health"
```

### Other Endpoints

| Endpoint                    | Method | Description                        |
|-----------------------------|--------|------------------------------------|
| `/api/queue/remove`         | POST   | Remove from queue (body: `{md5}`)  |
| `/api/queue/clear`          | POST   | Clear entire queue                 |
| `/api/queue/pause`          | POST   | Toggle pause/resume                |
| `/api/queue/current/cancel` | POST   | Cancel current, requeue            |
| `/api/queue/current/remove` | POST   | Cancel current, remove             |
| `/api/history/clear`        | POST   | Clear download history             |
| `/api/history/retry`        | POST   | Retry a failed download            |
| `/api/logs`                 | GET    | Last 1000 log lines                |
| `/api/version`              | GET    | Server + script versions           |

## Tech Stack

- Python 3.14, Flask, Gunicorn, BeautifulSoup4
- Docker/Alpine Linux deployment
- Fast download via Anna's Archive membership API
- Mirror fallback with domain rotation (li, pm, in)
- FlareSolverr integration for Cloudflare bypass

## Key Paths

- `src/stacks/` — Python source
- `web/` — Frontend (HTML/CSS/JS)
- `web/tamper/stacks_extension.user.js` — Tampermonkey userscript
- `config/config.yaml` — Runtime configuration
- `docs/` — Full documentation
