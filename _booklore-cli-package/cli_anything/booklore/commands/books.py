"""Book management commands."""

import json as json_mod

import click

from cli_anything.booklore.formatting import output, success, error, format_book, format_book_list


@click.group()
def books():
    """Manage books."""
    pass


@books.command("list")
@click.option("--with-description", is_flag=True, help="Include book descriptions")
@click.pass_context
def list_books(ctx, with_description):
    """List all books."""
    client = ctx.obj["client"]
    params = {}
    if with_description:
        params["withDescription"] = "true"
    data = client.get("/api/v1/books", params=params)
    output(data, ctx, formatter=format_book_list)


@books.command()
@click.argument("book_id", type=int)
@click.option("--with-description", is_flag=True)
@click.pass_context
def get(ctx, book_id, with_description):
    """Get a book by ID."""
    client = ctx.obj["client"]
    params = {}
    if with_description:
        params["withDescription"] = "true"
    data = client.get(f"/api/v1/books/{book_id}", params=params)
    output(data, ctx, formatter=format_book)


@books.command()
@click.argument("book_id", type=int)
@click.option("--output-path", "-o", type=click.Path(), help="Save cover to file")
@click.pass_context
def cover(ctx, book_id, output_path):
    """Download a book's cover image."""
    client = ctx.obj["client"]
    resp = client.get_raw(f"/api/v1/books/{book_id}/cover")
    if output_path:
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        success(f"Cover saved to {output_path}", ctx)
    else:
        content_type = resp.headers.get("Content-Type", "unknown")
        size = len(resp.content)
        if ctx.obj.get("json"):
            output({"book_id": book_id, "content_type": content_type, "size_bytes": size}, ctx)
        else:
            click.echo(f"Cover: {content_type}, {size} bytes")
            click.echo("Use -o <path> to save to file")


@books.command()
@click.argument("book_id", type=int)
@click.option("--output-path", "-o", type=click.Path(), required=True, help="Save book to file")
@click.pass_context
def download(ctx, book_id, output_path):
    """Download a book file."""
    client = ctx.obj["client"]
    resp = client.get_raw(f"/api/v1/books/{book_id}/download")
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    size = resp.headers.get("Content-Length", "unknown")
    success(f"Book downloaded to {output_path} ({size} bytes)", ctx)


@books.command()
@click.argument("book_id", type=int)
@click.option("--output-path", "-o", type=click.Path(), required=True, help="Save content to file")
@click.pass_context
def content(ctx, book_id, output_path):
    """Get raw book content."""
    client = ctx.obj["client"]
    resp = client.get_raw(f"/api/v1/books/{book_id}/content")
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    success(f"Content saved to {output_path}", ctx)


@books.command("viewer-setting")
@click.argument("book_id", type=int)
@click.pass_context
def viewer_setting(ctx, book_id):
    """Get viewer settings for a book."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/books/{book_id}/viewer-setting")
    output(data, ctx)


@books.command("set-viewer-setting")
@click.argument("book_id", type=int)
@click.option("--settings-json", required=True, help="Viewer settings as JSON string")
@click.pass_context
def set_viewer_setting(ctx, book_id, settings_json):
    """Update viewer settings for a book."""
    client = ctx.obj["client"]
    try:
        settings = json_mod.loads(settings_json)
    except json_mod.JSONDecodeError as e:
        error(f"Invalid JSON: {e}", ctx)
    client.put(f"/api/v1/books/{book_id}/viewer-setting", json=settings)
    success(f"Viewer settings updated for book {book_id}", ctx)


@books.command("assign-shelves")
@click.option("--book-ids", required=True, help="Comma-separated book IDs")
@click.option("--assign", multiple=True, type=int, help="Shelf IDs to assign")
@click.option("--unassign", multiple=True, type=int, help="Shelf IDs to unassign")
@click.pass_context
def assign_shelves(ctx, book_ids, assign, unassign):
    """Assign or unassign shelves to books."""
    client = ctx.obj["client"]
    ids = [int(x.strip()) for x in book_ids.split(",")]
    body = {
        "bookIds": ids,
        "shelvesToAssign": list(assign),
        "shelvesToUnassign": list(unassign),
    }
    data = client.post("/api/v1/books/shelves", json=body)
    output(data, ctx, formatter=format_book_list)


@books.command("update-progress")
@click.argument("book_id", type=int)
@click.option("--pdf-progress", type=int, help="PDF page number (0-100)")
@click.option("--epub-progress", help="EPUB progress (CFI string)")
@click.pass_context
def update_progress(ctx, book_id, pdf_progress, epub_progress):
    """Update reading progress for a book."""
    if pdf_progress is None and epub_progress is None:
        error("Provide --pdf-progress or --epub-progress", ctx)
    client = ctx.obj["client"]
    body = {"bookId": book_id}
    if pdf_progress is not None:
        body["pdfProgress"] = pdf_progress
    if epub_progress is not None:
        body["epubProgress"] = epub_progress
    client.post("/api/v1/books/progress", json=body)
    success(f"Progress updated for book {book_id}", ctx)
