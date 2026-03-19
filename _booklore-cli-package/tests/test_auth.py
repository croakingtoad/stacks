"""Tests for auth commands."""

import json

import responses
from click.testing import CliRunner

from cli_anything.booklore.main import cli


@responses.activate
def test_login_success(runner, temp_config):
    responses.post(
        "http://localhost:6060/api/v1/auth/login",
        json={"accessToken": "new.access.token", "refreshToken": "new.refresh.token"},
        status=200,
    )
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "auth", "login",
        "--username", "admin",
        "--password", "secret",
    ])
    assert result.exit_code == 0
    assert "Logged in" in result.output


@responses.activate
def test_login_failure(runner, temp_config):
    responses.post(
        "http://localhost:6060/api/v1/auth/login",
        json={"error": "Invalid credentials"},
        status=401,
    )
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "auth", "login",
        "--username", "admin",
        "--password", "wrong",
    ])
    assert result.exit_code != 0


@responses.activate
def test_login_json_output(runner, temp_config):
    responses.post(
        "http://localhost:6060/api/v1/auth/login",
        json={"accessToken": "tok", "refreshToken": "ref"},
        status=200,
    )
    result = runner.invoke(cli, [
        "--json",
        "--base-url", "http://localhost:6060",
        "auth", "login",
        "--username", "admin",
        "--password", "secret",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_auth_status_not_authenticated(runner, temp_config):
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "auth", "status",
    ])
    assert result.exit_code == 0
    assert "Not authenticated" in result.output


def test_logout(runner, temp_config, mock_session):
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "auth", "logout",
    ])
    assert result.exit_code == 0
    assert "Logged out" in result.output
