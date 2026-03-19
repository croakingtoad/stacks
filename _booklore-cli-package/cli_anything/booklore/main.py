"""BookLore CLI — main entry point."""

import click

from cli_anything.booklore import __version__
from cli_anything.booklore.models import Session
from cli_anything.booklore.client import Client
from cli_anything.booklore.commands.auth import auth
from cli_anything.booklore.commands.books import books
from cli_anything.booklore.commands.metadata import metadata
from cli_anything.booklore.commands.shelves import shelves
from cli_anything.booklore.commands.libraries import libraries
from cli_anything.booklore.commands.users import users
from cli_anything.booklore.commands.authors import authors
from cli_anything.booklore.commands.files import files
from cli_anything.booklore.commands.settings import settings
from cli_anything.booklore.commands.paths import paths


@click.group()
@click.option("--json", "use_json", is_flag=True, help="Output as JSON (for agent consumption)")
@click.option("--base-url", envvar="BOOKLORE_URL", help="BookLore server URL")
@click.version_option(version=__version__, prog_name="booklore-cli")
@click.pass_context
def cli(ctx, use_json, base_url):
    """BookLore CLI — manage your book collection from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json
    session = Session.load(base_url_override=base_url)
    ctx.obj["session"] = session
    ctx.obj["client"] = Client(session)


cli.add_command(auth)
cli.add_command(books)
cli.add_command(metadata)
cli.add_command(shelves)
cli.add_command(libraries)
cli.add_command(users)
cli.add_command(authors)
cli.add_command(files)
cli.add_command(settings)
cli.add_command(paths)


@cli.command()
@click.pass_context
def repl(ctx):
    """Launch interactive REPL mode."""
    from cli_anything.booklore.repl import run_repl
    run_repl(ctx)


if __name__ == "__main__":
    cli()
