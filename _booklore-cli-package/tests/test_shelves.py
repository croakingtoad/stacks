"""Tests for shelf commands."""

import json

import responses
from click.testing import CliRunner

from cli_anything.booklore.main import cli


SAMPLE_SHELF = {"id": 1, "name": "Science Fiction", "icon": "rocket"}


@responses.activate
def test_shelves_list(runner, temp_config, mock_session):
    responses.get(
        "http://localhost:6060/api/v1/shelves",
        json=[SAMPLE_SHELF],
        status=200,
    )
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "shelves", "list",
    ])
    assert result.exit_code == 0
    assert "Science Fiction" in result.output


@responses.activate
def test_shelves_create(runner, temp_config, mock_session):
    responses.post(
        "http://localhost:6060/api/v1/shelves",
        json={"id": 2, "name": "Fantasy", "icon": "wand"},
        status=201,
    )
    result = runner.invoke(cli, [
        "--json",
        "--base-url", "http://localhost:6060",
        "shelves", "create",
        "--name", "Fantasy",
        "--icon", "wand",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "Fantasy"


@responses.activate
def test_shelves_delete(runner, temp_config, mock_session):
    responses.delete(
        "http://localhost:6060/api/v1/shelves/1",
        status=204,
    )
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "shelves", "delete", "1",
    ])
    assert result.exit_code == 0
    assert "deleted" in result.output
