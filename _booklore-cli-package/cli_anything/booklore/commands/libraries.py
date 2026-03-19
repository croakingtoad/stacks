"""Library management commands."""

import json as json_mod

import click

from cli_anything.booklore.formatting import output, success, error, format_library, format_library_list, format_book, format_book_list


@click.group()
def libraries():
    """Manage libraries."""
    pass


@libraries.command("list")
@click.pass_context
def list_libraries(ctx):
    """List all libraries."""
    client = ctx.obj["client"]
    data = client.get("/api/v1/libraries")
    output(data, ctx, formatter=format_library_list)


@libraries.command()
@click.argument("library_id", type=int)
@click.pass_context
def get(ctx, library_id):
    """Get a library by ID."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/libraries/{library_id}")
    output(data, ctx, formatter=format_library)


@libraries.command()
@click.option("--name", required=True, help="Library name")
@click.option("--icon", required=True, help="Library icon")
@click.option("--path", "paths", required=True, multiple=True, help="Directory path(s)")
@click.option("--watch/--no-watch", default=False, help="Watch for changes")
@click.pass_context
def create(ctx, name, icon, paths, watch):
    """Create a new library."""
    client = ctx.obj["client"]
    body = {
        "name": name,
        "icon": icon,
        "paths": [{"path": p} for p in paths],
        "watch": watch,
    }
    data = client.post("/api/v1/libraries", json=body)
    output(data, ctx, formatter=format_library)


@libraries.command()
@click.argument("library_id", type=int)
@click.option("--name", required=True)
@click.option("--icon", required=True)
@click.option("--path", "paths", required=True, multiple=True)
@click.option("--watch/--no-watch", default=False)
@click.pass_context
def update(ctx, library_id, name, icon, paths, watch):
    """Update a library."""
    client = ctx.obj["client"]
    body = {
        "name": name,
        "icon": icon,
        "paths": [{"path": p} for p in paths],
        "watch": watch,
    }
    data = client.put(f"/api/v1/libraries/{library_id}", json=body)
    output(data, ctx, formatter=format_library)


@libraries.command()
@click.argument("library_id", type=int)
@click.pass_context
def delete(ctx, library_id):
    """Delete a library."""
    client = ctx.obj["client"]
    client.delete(f"/api/v1/libraries/{library_id}")
    success(f"Library {library_id} deleted", ctx)


@libraries.command("books")
@click.argument("library_id", type=int)
@click.pass_context
def library_books(ctx, library_id):
    """List all books in a library."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/libraries/{library_id}/book")
    output(data, ctx, formatter=format_book_list)


@libraries.command()
@click.argument("library_id", type=int)
@click.argument("book_id", type=int)
@click.pass_context
def book(ctx, library_id, book_id):
    """Get a specific book from a library."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/libraries/{library_id}/book/{book_id}")
    output(data, ctx, formatter=format_book)


@libraries.command()
@click.argument("library_id", type=int)
@click.pass_context
def rescan(ctx, library_id):
    """Rescan a library for new/changed books."""
    client = ctx.obj["client"]
    client.put(f"/api/v1/libraries/{library_id}/refresh")
    success(f"Library {library_id} rescan started", ctx)
