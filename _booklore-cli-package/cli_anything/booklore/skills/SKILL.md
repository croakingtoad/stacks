# Skill: BookLore CLI

## Overview

CLI tool for managing BookLore — a self-hosted web application for organizing
personal book collections. Wraps the BookLore REST API (Spring Boot + JWT auth).

## Installation

```bash
pip install -e /path/to/booklore-cli
```

## Configuration

Set `BOOKLORE_URL` environment variable or use `--base-url` flag.
Default: `http://localhost:6060`

## Authentication

```bash
booklore auth login --username admin --password admin123
```

Or set `BOOKLORE_USERNAME` and `BOOKLORE_PASSWORD` environment variables.
Tokens are stored in `~/.config/booklore-cli/session.json` and auto-refreshed.

## JSON Output

All commands support `--json` for structured output:
```bash
booklore --json books list
```

## Command Reference

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

## Agent Workflow Examples

### Catalog a new book
```bash
booklore --json auth login -u admin -p secret
booklore --json libraries list
booklore --json files upload /tmp/book.pdf --library-id 1 --path-id 1
booklore --json metadata search 42 --provider Google --title "Dune"
booklore --json metadata update 42 --metadata-json '{"title":"Dune","authors":["Frank Herbert"]}'
```

### Organize books into shelves
```bash
booklore --json shelves create --name "Science Fiction" --icon "rocket"
booklore --json books assign-shelves --book-ids 1,2,3 --assign 5
```

### Search and refresh metadata
```bash
booklore --json metadata refresh --type LIBRARY --library-id 1 --provider Google --refresh-covers
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Authentication error |
