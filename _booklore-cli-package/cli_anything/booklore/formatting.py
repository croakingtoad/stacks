"""Output formatting: JSON for agents, human-readable for terminals."""

import json
import sys

import click


def output(data, ctx, formatter=None):
    """Print data in JSON or human-readable format based on context."""
    if ctx.obj.get("json"):
        click.echo(json.dumps(data, indent=2, default=str))
    elif formatter and data is not None:
        formatter(data)
    elif data is not None:
        click.echo(json.dumps(data, indent=2, default=str))


def success(message, ctx):
    """Print a success message."""
    if ctx.obj.get("json"):
        click.echo(json.dumps({"success": True, "message": message}))
    else:
        click.echo(click.style(f"OK ", fg="green") + message)


def error(message, ctx, exit_code=1):
    """Print an error message and exit."""
    if ctx.obj.get("json"):
        click.echo(json.dumps({"success": False, "error": message}), err=True)
    else:
        click.echo(click.style(f"Error: ", fg="red") + message, err=True)
    sys.exit(exit_code)


def format_book(book):
    """Human-readable book display."""
    click.echo(click.style(f"[{book.get('id', '?')}] ", fg="cyan") + click.style(book.get("title") or book.get("fileName", "Untitled"), bold=True))
    meta = book.get("metadata") or {}
    if meta.get("authors"):
        authors = meta["authors"] if isinstance(meta["authors"], list) else [meta["authors"]]
        click.echo(f"  Authors: {', '.join(str(a) for a in authors)}")
    click.echo(f"  Type: {book.get('bookType', '?')}")
    if book.get("libraryId"):
        click.echo(f"  Library: {book['libraryId']}")
    shelves = book.get("shelves") or []
    if shelves:
        names = [s.get("name", str(s.get("id", "?"))) for s in shelves]
        click.echo(f"  Shelves: {', '.join(names)}")


def format_book_list(books):
    """Human-readable book list."""
    if not books:
        click.echo("No books found.")
        return
    click.echo(click.style(f"{len(books)} book(s):\n", bold=True))
    for book in books:
        format_book(book)
        click.echo()


def format_shelf(shelf):
    """Human-readable shelf display."""
    icon = shelf.get("icon", "")
    click.echo(click.style(f"[{shelf.get('id', '?')}] ", fg="cyan") + f"{icon} " + click.style(shelf.get("name", "Untitled"), bold=True))


def format_shelf_list(shelves):
    if not shelves:
        click.echo("No shelves found.")
        return
    for shelf in shelves:
        format_shelf(shelf)


def format_library(lib):
    """Human-readable library display."""
    icon = lib.get("icon", "")
    click.echo(click.style(f"[{lib.get('id', '?')}] ", fg="cyan") + f"{icon} " + click.style(lib.get("name", "Untitled"), bold=True))
    paths = lib.get("paths") or []
    for p in paths:
        path_str = p.get("path", p) if isinstance(p, dict) else p
        click.echo(f"  Path: {path_str}")
    if lib.get("watch"):
        click.echo("  Watching: yes")


def format_library_list(libs):
    if not libs:
        click.echo("No libraries found.")
        return
    for lib in libs:
        format_library(lib)
        click.echo()


def format_user(user):
    """Human-readable user display."""
    click.echo(click.style(f"[{user.get('id', '?')}] ", fg="cyan") + click.style(user.get("username", "?"), bold=True))
    if user.get("name"):
        click.echo(f"  Name: {user['name']}")
    if user.get("email"):
        click.echo(f"  Email: {user['email']}")
    perms = user.get("permissions") or {}
    if perms:
        flags = []
        if perms.get("isAdmin"):
            flags.append("admin")
        if perms.get("canUpload"):
            flags.append("upload")
        if perms.get("canDownload"):
            flags.append("download")
        if perms.get("canEditMetadata"):
            flags.append("edit-metadata")
        if flags:
            click.echo(f"  Permissions: {', '.join(flags)}")


def format_user_list(users):
    if not users:
        click.echo("No users found.")
        return
    for user in users:
        format_user(user)
        click.echo()


def format_metadata(meta):
    """Human-readable metadata display."""
    if meta.get("title"):
        click.echo(click.style(meta["title"], bold=True))
    if meta.get("subtitle"):
        click.echo(f"  Subtitle: {meta['subtitle']}")
    if meta.get("authors"):
        authors = meta["authors"] if isinstance(meta["authors"], list) else [meta["authors"]]
        click.echo(f"  Authors: {', '.join(str(a) for a in authors)}")
    if meta.get("publisher"):
        click.echo(f"  Publisher: {meta['publisher']}")
    if meta.get("publishedDate"):
        click.echo(f"  Published: {meta['publishedDate']}")
    if meta.get("isbn13"):
        click.echo(f"  ISBN-13: {meta['isbn13']}")
    if meta.get("isbn10"):
        click.echo(f"  ISBN-10: {meta['isbn10']}")
    if meta.get("pageCount"):
        click.echo(f"  Pages: {meta['pageCount']}")
    if meta.get("language"):
        click.echo(f"  Language: {meta['language']}")
    if meta.get("rating"):
        click.echo(f"  Rating: {meta['rating']}")
    if meta.get("categories"):
        click.echo(f"  Categories: {', '.join(str(c) for c in meta['categories'])}")
    if meta.get("description"):
        desc = meta["description"]
        if len(desc) > 200:
            desc = desc[:200] + "..."
        click.echo(f"  Description: {desc}")
