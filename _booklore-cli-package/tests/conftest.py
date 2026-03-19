"""Shared test fixtures."""

import base64
import json
import os
import tempfile
import time

import pytest
from click.testing import CliRunner

from cli_anything.booklore.main import cli
from cli_anything.booklore.models import Session


def make_fake_jwt(exp_offset=3600):
    """Create a fake JWT token that won't be detected as expired."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": "testuser", "exp": int(time.time()) + exp_offset}).encode()).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fakesignature").rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """Use a temp directory for config so tests don't pollute real config."""
    config_dir = tmp_path / "booklore-config"
    config_dir.mkdir()
    monkeypatch.setenv("BOOKLORE_CONFIG_DIR", str(config_dir))
    # Reload the module constants
    import cli_anything.booklore.models as models
    models.CONFIG_DIR = config_dir
    models.SESSION_FILE = config_dir / "session.json"
    return config_dir


@pytest.fixture
def mock_session(temp_config):
    """Create a mock session with fake tokens."""
    session = Session(
        base_url="http://localhost:6060",
        access_token=make_fake_jwt(),
        refresh_token=make_fake_jwt(),
        username="testuser",
    )
    session.save()
    return session


@pytest.fixture
def invoke(runner):
    """Helper to invoke CLI commands."""
    def _invoke(*args, catch_exceptions=False):
        return runner.invoke(cli, list(args), catch_exceptions=catch_exceptions)
    return _invoke
