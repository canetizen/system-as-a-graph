"""
Description: Outbound ports for LDAP authentication and session tokens (SRS VAE-01.3).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from vae.operations_panel.src.model.session import AuthenticatedUser, Session


class AuthenticationFailed(Exception):
    """Raised when a directory service refuses a credential.

    Carries no detail about *why* on purpose: telling a caller whether the
    account exists is an account-enumeration hint, and VAE-01.3 only requires
    that unsuccessful authentication be denied.
    """


@runtime_checkable
class DirectoryServicePort(Protocol):
    """Authenticates operators against the defined directory service (EXT-IF-06)."""

    def authenticate(self, username: str, password: str) -> AuthenticatedUser:
        """Bind as the given user and return who they are.

        Args:
            username: Directory account name.
            password: The account's password.

        Returns:
            The authenticated operator, carrying their authorizations.

        Raises:
            AuthenticationFailed: If the credential is not accepted.
        """
        ...


@runtime_checkable
class TokenServicePort(Protocol):
    """Issues and verifies the session token shared by the UI and the CLI.

    The token is stateless (SDP §5), so the panel keeps no session store: what
    a caller presents is the session.
    """

    def issue(self, user: AuthenticatedUser) -> tuple[str, Session]:
        """Issue a token for an authenticated operator.

        Args:
            user: The operator to issue for.

        Returns:
            The encoded token and the session it represents.
        """
        ...

    def verify(self, token: str) -> Session:
        """Decode and validate a token.

        Args:
            token: The encoded token.

        Returns:
            The session it carries.

        Raises:
            AuthenticationFailed: If the token is invalid, tampered with, or
                expired.
        """
        ...
