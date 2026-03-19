"""Path browsing commands."""

import click

from cli_anything.booklore.formatting import output


@click.group()
def paths():
    """Browse filesystem paths on the server."""
    pass


@paths.command("list")
@click.argument("path")
@click.pass_context
def list_paths(ctx, path):
    """List subdirectories at a given server path."""
    client = ctx.obj["client"]
    data = client.get("/api/v1/path", params={"path": path})
    if ctx.obj.get("json"):
        output(data, ctx)
    elif data:
        for entry in data:
            click.echo(entry)
    else:
        click.echo("No subdirectories found.")
