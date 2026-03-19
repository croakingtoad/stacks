"""Application settings commands."""

import json as json_mod

import click

from cli_anything.booklore.formatting import output, success, error


@click.group()
def settings():
    """Manage application settings."""
    pass


@settings.command("get")
@click.pass_context
def get_settings(ctx):
    """Get current application settings."""
    client = ctx.obj["client"]
    data = client.get("/api/v1/settings")
    output(data, ctx)


@settings.command()
@click.option("--category", required=True, help="Setting category")
@click.option("--name", required=True, help="Setting name")
@click.option("--value", required=True, help="Setting value (JSON)")
@click.pass_context
def update(ctx, category, name, value):
    """Update a setting."""
    client = ctx.obj["client"]
    try:
        parsed_value = json_mod.loads(value)
    except json_mod.JSONDecodeError:
        parsed_value = value
    body = {
        "category": category,
        "name": name,
        "value": parsed_value,
    }
    client.put("/api/v1/settings", json=body)
    success(f"Setting {category}.{name} updated", ctx)
