"""Tests for the HTTP client."""

import pytest
import responses

from cli_anything.booklore.client import Client, BookLoreError
from cli_anything.booklore.models import Session


@responses.activate
def test_get_json(temp_config):
    session = Session("http://localhost:6060", access_token="tok")
    client = Client(session)
    responses.get(
        "http://localhost:6060/api/v1/shelves",
        json=[{"id": 1, "name": "Test"}],
        status=200,
    )
    data = client.get("/api/v1/shelves")
    assert len(data) == 1
    assert data[0]["name"] == "Test"


@responses.activate
def test_post_json(temp_config):
    session = Session("http://localhost:6060", access_token="tok")
    client = Client(session)
    responses.post(
        "http://localhost:6060/api/v1/shelves",
        json={"id": 2, "name": "New"},
        status=201,
    )
    data = client.post("/api/v1/shelves", json={"name": "New", "icon": "x"})
    assert data["id"] == 2


@responses.activate
def test_delete_204(temp_config):
    session = Session("http://localhost:6060", access_token="tok")
    client = Client(session)
    responses.delete(
        "http://localhost:6060/api/v1/shelves/1",
        status=204,
    )
    result = client.delete("/api/v1/shelves/1")
    assert result is None


@responses.activate
def test_error_raises(temp_config):
    session = Session("http://localhost:6060", access_token="tok")
    client = Client(session)
    responses.get(
        "http://localhost:6060/api/v1/books/999",
        json={"error": "Not found"},
        status=404,
    )
    with pytest.raises(BookLoreError) as exc_info:
        client.get("/api/v1/books/999")
    assert exc_info.value.status_code == 404
