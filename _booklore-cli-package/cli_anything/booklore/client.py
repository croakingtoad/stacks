"""HTTP client for BookLore API with JWT auth and auto-refresh."""

import sys

import click
import requests


class BookLoreError(Exception):
    """API error with status code and message."""

    def __init__(self, status_code, message, response=None):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"HTTP {status_code}: {message}")


class Client:
    """Requests-based HTTP client for BookLore API."""

    def __init__(self, session):
        self.session = session
        self.base_url = session.base_url
        self._http = requests.Session()
        self._http.headers["Accept"] = "application/json"

    def _auth_headers(self):
        if self.session.access_token:
            return {"Authorization": f"Bearer {self.session.access_token}"}
        return {}

    def _ensure_auth(self):
        """Auto-refresh token if expired."""
        if self.session.is_token_expired() and self.session.refresh_token:
            self._refresh_token()

    def _refresh_token(self):
        """Attempt to refresh the JWT access token."""
        try:
            resp = self._http.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refreshToken": self.session.refresh_token},
            )
            if resp.status_code == 200:
                data = resp.json()
                self.session.set_tokens(
                    access_token=data.get("accessToken", data.get("access_token")),
                    refresh_token=data.get("refreshToken", data.get("refresh_token", self.session.refresh_token)),
                )
            else:
                click.echo("Session expired. Please run: booklore auth login", err=True)
                sys.exit(2)
        except requests.ConnectionError:
            click.echo(f"Cannot connect to BookLore at {self.base_url}", err=True)
            sys.exit(1)

    def _request(self, method, path, **kwargs):
        """Make an authenticated request, handling errors."""
        self._ensure_auth()
        url = f"{self.base_url}{path}"
        headers = {**self._auth_headers(), **kwargs.pop("headers", {})}
        try:
            resp = self._http.request(method, url, headers=headers, **kwargs)
        except requests.ConnectionError:
            click.echo(f"Cannot connect to BookLore at {self.base_url}", err=True)
            sys.exit(1)

        if resp.status_code == 401:
            # Try refresh once
            if self.session.refresh_token:
                self._refresh_token()
                headers = {**self._auth_headers(), **kwargs.pop("headers", {})}
                resp = self._http.request(method, url, headers=headers, **kwargs)
                if resp.status_code == 401:
                    click.echo("Authentication failed. Please run: booklore auth login", err=True)
                    sys.exit(2)
            else:
                click.echo("Not authenticated. Please run: booklore auth login", err=True)
                sys.exit(2)

        if resp.status_code == 204:
            return None

        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise BookLoreError(resp.status_code, detail, resp)

        return resp

    def get(self, path, params=None):
        """GET request, return parsed JSON."""
        resp = self._request("GET", path, params=params)
        if resp is None:
            return None
        return resp.json()

    def post(self, path, json=None, **kwargs):
        """POST request, return parsed JSON."""
        resp = self._request("POST", path, json=json, **kwargs)
        if resp is None:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

    def put(self, path, json=None):
        """PUT request, return parsed JSON or None."""
        resp = self._request("PUT", path, json=json)
        if resp is None:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

    def delete(self, path):
        """DELETE request."""
        self._request("DELETE", path)
        return None

    def get_raw(self, path, params=None):
        """GET request returning raw Response (for binary data)."""
        self._ensure_auth()
        url = f"{self.base_url}{path}"
        headers = self._auth_headers()
        try:
            resp = self._http.get(url, headers=headers, params=params, stream=True)
        except requests.ConnectionError:
            click.echo(f"Cannot connect to BookLore at {self.base_url}", err=True)
            sys.exit(1)
        if resp.status_code >= 400:
            raise BookLoreError(resp.status_code, resp.text, resp)
        return resp

    def post_file(self, path, files, data=None):
        """POST with multipart file upload."""
        self._ensure_auth()
        url = f"{self.base_url}{path}"
        headers = self._auth_headers()
        try:
            resp = self._http.post(url, headers=headers, files=files, data=data)
        except requests.ConnectionError:
            click.echo(f"Cannot connect to BookLore at {self.base_url}", err=True)
            sys.exit(1)
        if resp.status_code >= 400:
            raise BookLoreError(resp.status_code, resp.text, resp)
        try:
            return resp.json()
        except ValueError:
            return None
