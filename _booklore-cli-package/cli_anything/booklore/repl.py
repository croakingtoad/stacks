"""Interactive REPL for BookLore CLI."""

import shlex
import sys
from importlib.resources import files as pkg_files
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from cli_anything.booklore import __version__
from cli_anything.booklore.models import CONFIG_DIR


REPL_HISTORY = CONFIG_DIR / "repl_history"


def get_skill_path():
    """Find the SKILL.md file path."""
    try:
        skill_dir = pkg_files("cli_anything.booklore") / "skills"
        skill_path = skill_dir / "SKILL.md"
        if Path(str(skill_path)).exists():
            return str(skill_path)
    except (TypeError, FileNotFoundError):
        pass
    # Fallback: relative to this file
    here = Path(__file__).parent / "skills" / "SKILL.md"
    if here.exists():
        return str(here)
    return None


def get_commands():
    """Get all available command names for tab completion."""
    from cli_anything.booklore.main import cli
    commands = []
    for name, cmd in cli.commands.items():
        commands.append(name)
        if hasattr(cmd, "commands"):
            for sub_name in cmd.commands:
                commands.append(f"{name} {sub_name}")
    return commands


def run_repl(ctx):
    """Launch the interactive REPL."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    skill_path = get_skill_path()
    click.echo(click.style(f"BookLore CLI v{__version__}", bold=True))
    click.echo(f"Server: {ctx.obj['session'].base_url}")
    if skill_path:
        click.echo(f"Skill file: {skill_path}")
    if ctx.obj["session"].username:
        click.echo(f"User: {ctx.obj['session'].username}")
    click.echo("Type 'help' for commands, 'exit' to quit.\n")

    completer = WordCompleter(get_commands(), sentence=True)
    session = PromptSession(
        history=FileHistory(str(REPL_HISTORY)),
        completer=completer,
    )

    from cli_anything.booklore.main import cli

    while True:
        try:
            line = session.prompt("booklore> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\nBye!")
            break

        if not line:
            continue
        if line in ("exit", "quit", "q"):
            click.echo("Bye!")
            break
        if line == "help":
            # Show top-level help
            try:
                cli.main(["--help"], standalone_mode=False)
            except SystemExit:
                pass
            continue

        try:
            args = shlex.split(line)
        except ValueError as e:
            click.echo(f"Parse error: {e}")
            continue

        # Prepend global flags from context
        if ctx.obj.get("json"):
            args = ["--json"] + args

        try:
            cli.main(args, standalone_mode=False)
        except SystemExit:
            pass
        except click.exceptions.UsageError as e:
            click.echo(f"Usage error: {e}")
        except Exception as e:
            click.echo(click.style(f"Error: {e}", fg="red"))
