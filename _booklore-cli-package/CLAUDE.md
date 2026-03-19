# BookLore CLI

## Overview

Python CLI tool wrapping the BookLore REST API (Spring Boot backend).
Follows CLI-Anything patterns: Click framework, `--json` output, REPL mode, SKILL.md.

## Tech Stack

- Python 3.10+, Click 8.0+, requests, prompt-toolkit, PyJWT
- BookLore backend: Spring Boot + MariaDB (JWT auth)

## Key Paths

- `cli_anything/booklore/` — Main package
- `cli_anything/booklore/commands/` — Click command groups
- `cli_anything/booklore/skills/SKILL.md` — AI-discoverable capabilities
- `tests/` — pytest test suite

## Environment Variables

- `BOOKLORE_URL` — BookLore server URL (default: http://localhost:6060)
- `BOOKLORE_USERNAME` — Login username
- `BOOKLORE_PASSWORD` — Login password

## Commands

```
booklore auth login          # Authenticate
booklore books list          # List all books
booklore shelves create      # Create a shelf
booklore libraries list      # List libraries
booklore metadata search     # Search metadata providers
```

All commands support `--json` for structured agent output.

## Development

```bash
pip install -e ".[dev]"
pytest
```
