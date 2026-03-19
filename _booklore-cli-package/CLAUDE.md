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
- `cli_anything/booklore/skills/SKILL.md` — Full AI-discoverable command reference
- `tests/` — pytest test suite

## Environment Variables

- `BOOKLORE_URL` — BookLore server URL (default: http://localhost:6060)
- `BOOKLORE_USERNAME` — Login username
- `BOOKLORE_PASSWORD` — Login password

## Stacks / Librarian Integration

This CLI is used as an optional integration from the **Stacks** download manager's
`/librarian` agent skill. After Stacks downloads a book from Anna's Archive, the
librarian agent can use this CLI to catalog it in BookLore.

The Stacks librarian skill lives in `croakingtoad/stacks` at
`.claude/commands/librarian.md` and references this CLI's SKILL.md for the full
command reference.

Typical post-download workflow:
```bash
booklore --json libraries rescan LIB_ID          # Pick up new file
booklore --json books list                        # Find new book
booklore --json metadata search BOOK_ID --provider Google  # Fetch metadata
booklore --json books assign-shelves --book-ids ID --assign SHELF_ID  # Organize
```

## Command Reference

All commands support `--json` for structured agent output.

### auth — Authentication & Session

| Command | Description |
|---------|-------------|
| `auth login -u USER -p PASS` | Log in and store JWT tokens |
| `auth logout` | Clear stored session |
| `auth me` | Show current user profile |
| `auth status` | Check authentication status |
| `auth register --username U --password P --name N --email E` | Register user (admin) |
| `auth refresh` | Manually refresh access token |

### books — Book Management

| Command | Description |
|---------|-------------|
| `books list [--with-description]` | List all books |
| `books get BOOK_ID [--with-description]` | Get book details |
| `books cover BOOK_ID [-o FILE]` | Download cover image |
| `books download BOOK_ID -o FILE` | Download book file |
| `books content BOOK_ID -o FILE` | Get raw book content |
| `books viewer-setting BOOK_ID` | Get viewer settings |
| `books set-viewer-setting BOOK_ID --settings-json JSON` | Update viewer settings |
| `books assign-shelves --book-ids 1,2 --assign 3 --unassign 4` | Assign/unassign shelves |
| `books update-progress BOOK_ID --pdf-progress N` | Update reading progress |

### metadata — Metadata Management

| Command | Description |
|---------|-------------|
| `metadata search BOOK_ID [--provider Google] [--isbn X] [--title X] [--author X]` | Search metadata providers |
| `metadata update BOOK_ID --metadata-json JSON` | Update book metadata |
| `metadata refresh --type BOOKS\|LIBRARY [--book-ids 1,2] [--library-id N]` | Schedule metadata refresh |
| `metadata upload-cover BOOK_ID FILE` | Upload cover image |
| `metadata lock BOOK_ID --field FIELD [--locked\|--unlocked]` | Lock/unlock metadata field |

### shelves — Shelf Management

| Command | Description |
|---------|-------------|
| `shelves list` | List all shelves |
| `shelves get SHELF_ID` | Get shelf details |
| `shelves create --name NAME --icon ICON` | Create a shelf |
| `shelves update SHELF_ID --name NAME --icon ICON` | Update a shelf |
| `shelves delete SHELF_ID` | Delete a shelf |
| `shelves books SHELF_ID` | List books in a shelf |

### libraries — Library Management

| Command | Description |
|---------|-------------|
| `libraries list` | List all libraries |
| `libraries get LIBRARY_ID` | Get library details |
| `libraries create --name N --icon I --path /dir [--watch]` | Create a library |
| `libraries update LIBRARY_ID --name N --icon I --path /dir` | Update a library |
| `libraries delete LIBRARY_ID` | Delete a library |
| `libraries books LIBRARY_ID` | List books in a library |
| `libraries book LIBRARY_ID BOOK_ID` | Get a specific book from library |
| `libraries rescan LIBRARY_ID` | Rescan library for changes |

### users — User Management (Admin)

| Command | Description |
|---------|-------------|
| `users list` | List all users |
| `users get USER_ID` | Get user details |
| `users update USER_ID [--name N] [--email E] [--can-upload]` | Update user |
| `users delete USER_ID` | Delete user |
| `users change-password` | Change own password |
| `users change-user-password USER_ID --new-password P` | Change user's password |
| `users set-book-preferences USER_ID --preferences-json JSON` | Update reader preferences |

### authors — Author Queries

| Command | Description |
|---------|-------------|
| `authors for-book BOOK_ID` | Get authors for a book |

### files — File Upload

| Command | Description |
|---------|-------------|
| `files upload FILE --library-id N --path-id N` | Upload book file |

### settings — App Settings

| Command | Description |
|---------|-------------|
| `settings get` | Get current settings |
| `settings update --category C --name N --value V` | Update a setting |

### paths — Server Path Browsing

| Command | Description |
|---------|-------------|
| `paths list /some/path` | List subdirectories at path |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Authentication error |
