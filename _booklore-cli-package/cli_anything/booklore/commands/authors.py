"""Author commands."""

import click

from cli_anything.booklore.formatting import output


@click.group()
def authors():
    """Query authors."""
    pass


@authors.command("for-book")
@click.argument("book_id", type=int)
@click.pass_context
def for_book(ctx, book_id):
    """Get authors for a specific book."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/authors/book/{book_id}")
    if ctx.obj.get("json"):
        output(data, ctx)
    elif data:
        click.echo(", ".join(str(a) for a in data))
    else:
        click.echo("No authors found.")
