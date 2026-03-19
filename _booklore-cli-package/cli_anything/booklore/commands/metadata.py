"""Metadata management commands."""

import json as json_mod

import click

from cli_anything.booklore.formatting import output, success, error, format_metadata


@click.group()
def metadata():
    """Manage book metadata."""
    pass


@metadata.command()
@click.argument("book_id", type=int)
@click.option("--provider", multiple=True, type=click.Choice(["Amazon", "GoodReads", "Google"]), help="Metadata providers to search")
@click.option("--isbn", help="Search by ISBN")
@click.option("--title", help="Search by title")
@click.option("--author", help="Search by author")
@click.pass_context
def search(ctx, book_id, provider, isbn, title, author):
    """Search metadata providers for a book."""
    client = ctx.obj["client"]
    body = {"bookId": book_id}
    if provider:
        body["providers"] = list(provider)
    if isbn:
        body["isbn"] = isbn
    if title:
        body["title"] = title
    if author:
        body["author"] = author
    data = client.post(f"/api/v1/books/{book_id}/metadata/prospective", json=body)
    if ctx.obj.get("json"):
        output(data, ctx)
    elif data:
        for i, meta in enumerate(data):
            click.echo(click.style(f"\n--- Result {i + 1} ---", fg="yellow"))
            format_metadata(meta)
    else:
        click.echo("No metadata results found.")


@metadata.command()
@click.argument("book_id", type=int)
@click.option("--metadata-json", required=True, help="Metadata as JSON string")
@click.option("--merge-categories/--no-merge-categories", default=True)
@click.pass_context
def update(ctx, book_id, metadata_json, merge_categories):
    """Update book metadata."""
    client = ctx.obj["client"]
    try:
        meta = json_mod.loads(metadata_json)
    except json_mod.JSONDecodeError as e:
        error(f"Invalid JSON: {e}", ctx)
    params = {"mergeCategories": str(merge_categories).lower()}
    data = client.put(f"/api/v1/books/{book_id}/metadata", json=meta)
    output(data, ctx, formatter=format_metadata)


@metadata.command("refresh")
@click.option("--type", "refresh_type", required=True, type=click.Choice(["BOOKS", "LIBRARY"]))
@click.option("--library-id", type=int, help="Library ID (for LIBRARY type)")
@click.option("--book-ids", help="Comma-separated book IDs (for BOOKS type)")
@click.option("--quick", is_flag=True, default=False)
@click.option("--provider", "primary_provider", type=click.Choice(["Amazon", "GoodReads", "Google"]), default="Google")
@click.option("--refresh-covers", is_flag=True, default=False)
@click.option("--merge-categories", is_flag=True, default=True)
@click.pass_context
def refresh_metadata(ctx, refresh_type, library_id, book_ids, quick, primary_provider, refresh_covers, merge_categories):
    """Schedule a metadata refresh for books or a library."""
    client = ctx.obj["client"]
    body = {
        "refreshType": refresh_type,
        "quick": quick,
        "refreshOptions": {
            "allP1": primary_provider,
            "refreshCovers": refresh_covers,
            "mergeCategories": merge_categories,
        },
    }
    if library_id:
        body["libraryId"] = library_id
    if book_ids:
        body["bookIds"] = [int(x.strip()) for x in book_ids.split(",")]
    client.put("/api/v1/books/metadata/refresh", json=body)
    success("Metadata refresh scheduled", ctx)


@metadata.command("upload-cover")
@click.argument("book_id", type=int)
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def upload_cover(ctx, book_id, file_path):
    """Upload a cover image for a book."""
    client = ctx.obj["client"]
    with open(file_path, "rb") as f:
        data = client.post_file(
            f"/api/v1/books/{book_id}/metadata/cover",
            files={"file": f},
        )
    output(data, ctx, formatter=format_metadata)


@metadata.command()
@click.argument("book_id", type=int)
@click.option("--field", required=True, help="Field name to lock/unlock")
@click.option("--locked/--unlocked", default=True)
@click.pass_context
def lock(ctx, book_id, field, locked):
    """Lock or unlock a metadata field."""
    client = ctx.obj["client"]
    body = {
        "bookId": book_id,
        "field": field,
        "isLocked": locked,
    }
    data = client.put(f"/api/v1/books/{book_id}/metadata/lock", json=body)
    output(data, ctx, formatter=format_metadata)
