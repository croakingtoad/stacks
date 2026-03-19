"""File upload commands."""

import click

from cli_anything.booklore.formatting import output, success, format_book


@click.group()
def files():
    """Upload book files."""
    pass


@files.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--library-id", required=True, type=int, help="Target library ID")
@click.option("--path-id", required=True, type=int, help="Target path ID within library")
@click.pass_context
def upload(ctx, file_path, library_id, path_id):
    """Upload a book file (PDF or EPUB) to a library."""
    client = ctx.obj["client"]
    with open(file_path, "rb") as f:
        data = client.post_file(
            "/api/v1/files/upload",
            files={"file": f},
            data={"libraryId": str(library_id), "pathId": str(path_id)},
        )
    output(data, ctx, formatter=format_book)
