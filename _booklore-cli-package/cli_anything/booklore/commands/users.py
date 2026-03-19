"""User management commands."""

import json as json_mod

import click

from cli_anything.booklore.formatting import output, success, error, format_user, format_user_list


@click.group()
def users():
    """Manage users (admin)."""
    pass


@users.command("list")
@click.pass_context
def list_users(ctx):
    """List all users (admin only)."""
    client = ctx.obj["client"]
    data = client.get("/api/v1/users")
    output(data, ctx, formatter=format_user_list)


@users.command()
@click.argument("user_id", type=int)
@click.pass_context
def get(ctx, user_id):
    """Get a user by ID."""
    client = ctx.obj["client"]
    data = client.get(f"/api/v1/users/{user_id}")
    output(data, ctx, formatter=format_user)


@users.command()
@click.argument("user_id", type=int)
@click.option("--name", help="User display name")
@click.option("--email", help="User email")
@click.option("--can-upload/--no-upload", default=None)
@click.option("--can-download/--no-download", default=None)
@click.option("--can-edit-metadata/--no-edit-metadata", default=None)
@click.option("--library-ids", help="Comma-separated library IDs")
@click.pass_context
def update(ctx, user_id, name, email, can_upload, can_download, can_edit_metadata, library_ids):
    """Update a user (admin only)."""
    client = ctx.obj["client"]
    body = {}
    if name:
        body["name"] = name
    if email:
        body["email"] = email
    perms = {}
    if can_upload is not None:
        perms["canUpload"] = can_upload
    if can_download is not None:
        perms["canDownload"] = can_download
    if can_edit_metadata is not None:
        perms["canEditMetadata"] = can_edit_metadata
    if perms:
        body["permissions"] = perms
    if library_ids:
        body["assignedLibraries"] = [int(x.strip()) for x in library_ids.split(",")]
    data = client.put(f"/api/v1/users/{user_id}", json=body)
    output(data, ctx, formatter=format_user)


@users.command()
@click.argument("user_id", type=int)
@click.pass_context
def delete(ctx, user_id):
    """Delete a user (admin only)."""
    client = ctx.obj["client"]
    client.delete(f"/api/v1/users/{user_id}")
    success(f"User {user_id} deleted", ctx)


@users.command("change-password")
@click.option("--current-password", prompt=True, hide_input=True)
@click.option("--new-password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_context
def change_password(ctx, current_password, new_password):
    """Change your own password."""
    client = ctx.obj["client"]
    body = {
        "currentPassword": current_password,
        "newPassword": new_password,
    }
    client.put("/api/v1/users/change-password", json=body)
    success("Password changed", ctx)


@users.command("change-user-password")
@click.argument("user_id", type=int)
@click.option("--new-password", required=True)
@click.pass_context
def change_user_password(ctx, user_id, new_password):
    """Change another user's password (admin only)."""
    client = ctx.obj["client"]
    body = {
        "userId": user_id,
        "newPassword": new_password,
    }
    client.put("/api/v1/users/change-user-password", json=body)
    success(f"Password changed for user {user_id}", ctx)


@users.command("set-book-preferences")
@click.argument("user_id", type=int)
@click.option("--preferences-json", required=True, help="Preferences as JSON string")
@click.pass_context
def set_book_preferences(ctx, user_id, preferences_json):
    """Update book reader preferences for a user."""
    client = ctx.obj["client"]
    try:
        prefs = json_mod.loads(preferences_json)
    except json_mod.JSONDecodeError as e:
        error(f"Invalid JSON: {e}", ctx)
    client.put(f"/api/v1/users/{user_id}/book-preferences", json=prefs)
    success(f"Book preferences updated for user {user_id}", ctx)
