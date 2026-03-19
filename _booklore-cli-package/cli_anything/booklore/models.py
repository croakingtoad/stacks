"""Session and token management for BookLore CLI."""

import base64
import json
import os
import time
from pathlib import Path


CONFIG_DIR = Path(os.environ.get("BOOKLORE_CONFIG_DIR", "~/.config/booklore-cli")).expanduser()
SESSION_FILE = CONFIG_DIR / "session.json"

DEFAULT_URL = "http://localhost:6060"


class Session:
    """Manages JWT auth state with auto-refresh."""

    def __init__(self, base_url, access_token=None, refresh_token=None, username=None):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.username = username

    @classmethod
    def load(cls, base_url_override=None):
        """Load session from disk, applying URL override if given."""
        base_url = base_url_override or os.environ.get("BOOKLORE_URL", DEFAULT_URL)
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())
                return cls(
                    base_url=base_url_override or data.get("base_url", base_url),
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    username=data.get("username"),
                )
            except (json.JSONDecodeError, KeyError):
                pass
        return cls(base_url=base_url)

    def save(self):
        """Persist session to disk with restricted permissions."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "base_url": self.base_url,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "username": self.username,
        }
        SESSION_FILE.write_text(json.dumps(data, indent=2))
        SESSION_FILE.chmod(0o600)

    def is_token_expired(self):
        """Check if the access token JWT is expired (or missing)."""
        if not self.access_token:
            return True
        try:
            # Decode JWT payload without external library
            parts = self.access_token.split(".")
            if len(parts) != 3:
                return True
            # Add padding for base64
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            exp = payload.get("exp")
            if exp is None:
                return False
            # Consider expired if within 30 seconds of expiry
            return time.time() > (exp - 30)
        except (ValueError, json.JSONDecodeError, IndexError):
            return True

    @property
    def is_authenticated(self):
        return self.access_token is not None

    def set_tokens(self, access_token, refresh_token, username=None):
        """Store new tokens and persist."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        if username:
            self.username = username
        self.save()

    def clear(self):
        """Remove stored session."""
        self.access_token = None
        self.refresh_token = None
        self.username = None
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
