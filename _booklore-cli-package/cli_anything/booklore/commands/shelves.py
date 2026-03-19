"""Shelf management commands."""

import click

from cli_anything.booklore.formatting import output, success, format_shelf, format_shelf_list, format_book_list


@click.group()
def shelves():
    """Manage shelves (book collections)."""
    pass


@shelves.command("list")
@click.pass_context
def list_shelves(ctx):
    """List all shelves."""
    client = ctx.obj["client"]
    data = client.get("/api/v1/shelves")
    output(data, ctx, formatter=format_shelf_list)


@shelves.command()
@click.argument("shelf_id", type=int)
@click.pass_context
def get(ctx, shelf_id):
    """Get a shelf by ID."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/shelves/{shelf_id}")
    output(data, ctx, formatter=format_shelf)


@shelves.command()
@click.option("--name", required=True, help="Shelf name")
@click.option("--icon", required=True, help="Shelf icon")
@click.pass_context
def create(ctx, name, icon):
    """Create a new shelf."""
    client = ctx.obj["client"]
    body = {"id": None, "name": name, "icon": icon}
    data = client.post("/api/v1/shelves", json=body)
    output(data, ctx, formatter=format_shelf)


@shelves.command()
@click.argument("shelf_id", type=int)
@click.option("--name", required=True, help="New shelf name")
@click.option("--icon", required=True, help="New shelf icon")
@click.pass_context
def update(ctx, shelf_id, name, icon):
    """Update a shelf."""
    client = ctx.obj["client"]
    body = {"name": name, "icon": icon}
    data = client.put(f"/api/v1/shelves/{shelf_id}", json=body)
    output(data, ctx, formatter=format_shelf)


@shelves.command()
@click.argument("shelf_id", type=int)
@click.pass_context
def delete(ctx, shelf_id):
    """Delete a shelf."""
    client = ctx.obj["client"]
    client.delete(f"/api/v1/shelves/{shelf_id}")
    success(f"Shelf {shelf_id} deleted", ctx)


@shelves.command("books")
@click.argument("shelf_id", type=int)
@click.pass_context
def shelf_books(ctx, shelf_id):
    """List books in a shelf."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/shelves/{shelf_id}/books")
    output(data, ctx, formatter=format_book_list)
