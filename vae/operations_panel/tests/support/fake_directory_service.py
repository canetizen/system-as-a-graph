"""
Description: In-test directory service double, so panel tests need no LDAP server.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from vae.operations_panel.src.model.session import AuthenticatedUser, Authorization
from vae.operations_panel.src.ports.directory_service import AuthenticationFailed

#: Environment variable pointing at a replacement account file.
USERS_FILE_ENV_VAR = "VAE_TEST_USERS_FILE"

_DEFAULT_USERS_FILE = Path(__file__).resolve().parent / "users.json"


class FakeDirectoryService:
    """Authenticates against a local account file instead of an LDAP server.

    A test double, never wired into a running service: it behaves like a bind —
    the password is checked, a failure says nothing about why, and the
    account's authorizations come back with it — so a test written against it
    holds for the real ``ldap3`` adapter too.
    """

    def __init__(self, users_file: Path | None = None) -> None:
        """Initialize the adapter.

        Args:
            users_file: Account file; defaults to ``$VAE_FAKE_USERS_FILE`` and
                then to the file shipped inside the package.
        """
        self._path = Path(users_file or os.getenv(USERS_FILE_ENV_VAR) or _DEFAULT_USERS_FILE)

    def authenticate(self, username: str, password: str) -> AuthenticatedUser:
        """Check a credential against the account file.

        Args:
            username: Directory account name.
            password: The account's password.

        Returns:
            The authenticated operator with their authorizations.

        Raises:
            AuthenticationFailed: If the account is unknown, the password does
                not match, or the account file cannot be read.
        """
        for entry in self._accounts():
            if entry.get("username") == username and entry.get("password") == password:
                return AuthenticatedUser(
                    username=username,
                    display_name=entry.get("display_name", username),
                    authorizations=frozenset(
                        Authorization(value) for value in entry.get("authorizations", [])
                    ),
                )

        raise AuthenticationFailed("Authentication failed")

    def _accounts(self) -> list[dict]:
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                return json.load(handle).get("users", [])
        except (OSError, json.JSONDecodeError) as exc:
            raise AuthenticationFailed("Directory service is not available") from exc
