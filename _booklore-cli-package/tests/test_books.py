"""Tests for book commands."""

import json

import responses
from click.testing import CliRunner

from cli_anything.booklore.main import cli


SAMPLE_BOOK = {
    "id": 1,
    "title": "Dune",
    "bookType": "EPUB",
    "fileName": "dune.epub",
    "libraryId": 1,
    "metadata": {
        "title": "Dune",
        "authors": ["Frank Herbert"],
        "isbn13": "9780441013593",
    },
    "shelves": [{"id": 1, "name": "Science Fiction"}],
}


@responses.activate
def test_books_list(runner, temp_config, mock_session):
    responses.get(
        "http://localhost:6060/api/v1/books",
        json=[SAMPLE_BOOK],
        status=200,
    )
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "books", "list",
    ])
    assert result.exit_code == 0
    assert "Dune" in result.output


@responses.activate
def test_books_list_json(runner, temp_config, mock_session):
    responses.get(
        "http://localhost:6060/api/v1/books",
        json=[SAMPLE_BOOK],
        status=200,
    )
    result = runner.invoke(cli, [
        "--json",
        "--base-url", "http://localhost:6060",
        "books", "list",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["title"] == "Dune"


@responses.activate
def test_books_get(runner, temp_config, mock_session):
    responses.get(
        "http://localhost:6060/api/v1/books/1",
        json=SAMPLE_BOOK,
        status=200,
    )
    result = runner.invoke(cli, [
        "--json",
        "--base-url", "http://localhost:6060",
        "books", "get", "1",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == 1


@responses.activate
def test_books_update_progress(runner, temp_config, mock_session):
    responses.post(
        "http://localhost:6060/api/v1/books/progress",
        status=204,
    )
    result = runner.invoke(cli, [
        "--base-url", "http://localhost:6060",
        "books", "update-progress", "1",
        "--pdf-progress", "50",
    ])
    assert result.exit_code == 0
    assert "Progress updated" in result.output
