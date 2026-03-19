"""Authentication commands: login, register, refresh, me."""

import os

import click
import requests

from cli_anything.booklore.formatting import output, success, error, format_user


@click.group()
def auth():
    """Authentication and session management."""
    pass


@auth.command()
@click.option("--username", "-u", envvar="BOOKLORE_USERNAME", prompt=True)
@click.option("--password", "-p", envvar="BOOKLORE_PASSWORD", prompt=True, hide_input=True)
@click.pass_context
def login(ctx, username, password):
    """Log in to BookLore and store session tokens."""
    session = ctx.obj["session"]
    try:
        resp = requests.post(
            f"{session.base_url}/api/v1/auth/login",
            json={"username": username, "password": password},
        )
    except requests.ConnectionError:
        error(f"Cannot connect to BookLore at {session.base_url}", ctx)

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text
        error(f"Login failed: {detail}", ctx, exit_code=2)

    data = resp.json()
    access = data.get("accessToken") or data.get("access_token") or data.get("token")
    refresh = data.get("refreshToken") or data.get("refresh_token")
    if not access:
        error("Login response missing access token", ctx)

    session.set_tokens(access, refresh, username=username)
    success(f"Logged in as {username}", ctx)


@auth.command()
@click.option("--username", required=True)
@click.option("--password", required=True)
@click.option("--name", required=True)
@click.option("--email", required=True)
@click.option("--can-upload", is_flag=True, default=False)
@click.option("--can-download", is_flag=True, default=False)
@click.option("--can-edit-metadata", is_flag=True, default=False)
@click.option("--library-ids", multiple=True, type=int)
@click.pass_context
def register(ctx, username, password, name, email, can_upload, can_download, can_edit_metadata, library_ids):
    """Register a new user (admin only)."""
    client = ctx.obj["client"]
    body = {
        "username": username,
        "password": password,
        "name": name,
        "email": email,
        "permissionUpload": can_upload,
        "permissionDownload": can_download,
        "permissionEditMetadata": can_edit_metadata,
        "selectedLibraries": list(library_ids) if library_ids else [],
    }
    client.post("/api/v1/auth/register", json=body)
    success(f"User '{username}' registered", ctx)


@auth.command()
@click.pass_context
def refresh(ctx):
    """Manually refresh the access token."""
    session = ctx.obj["session"]
    if not session.refresh_token:
        error("No refresh token stored. Please login first.", ctx, exit_code=2)
    client = ctx.obj["client"]
    client._refresh_token()
    success("Token refreshed", ctx)


@auth.command()
@click.pass_context
def me(ctx):
    """Show current user profile."""
    client = ctx.obj["client"]
    data = client.get("/api/v1/users/me")
    output(data, ctx, formatter=format_user)


@auth.command()
@click.pass_context
def logout(ctx):
    """Clear stored session."""
    ctx.obj["session"].clear()
    success("Logged out", ctx)


@auth.command()
@click.pass_context
def status(ctx):
    """Check if currently authenticated."""
    session = ctx.obj["session"]
    if session.is_authenticated:
        expired = session.is_token_expired()
        info = {
            "authenticated": True,
            "username": session.username,
            "base_url": session.base_url,
            "token_expired": expired,
        }
        if ctx.obj.get("json"):
            output(info, ctx)
        else:
            click.echo(f"Authenticated as: {session.username or '?'}")
            click.echo(f"Server: {session.base_url}")
            click.echo(f"Token expired: {'yes' if expired else 'no'}")
    else:
        if ctx.obj.get("json"):
            output({"authenticated": False}, ctx)
        else:
            click.echo("Not authenticated. Run: booklore auth login")
