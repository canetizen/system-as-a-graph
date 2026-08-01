"""
Description: Stateless JWT session tokens shared by the web UI and the CLI.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import jwt

from vae.operations_panel.src.model.session import (
    AuthenticatedUser,
    Authorization,
    Session,
)
from vae.operations_panel.src.ports.directory_service import AuthenticationFailed
from vae.operations_panel.src.ports.support import ClockPort

#: Environment variable holding the signing secret (SDP §5: secrets live in
#: the environment). There is deliberately no fallback: a built-in default
#: would be a published signing key, and a service that starts with one is
#: worse than a service that refuses to start.
SECRET_ENV_VAR = "VAE_JWT_SECRET"

#: Shortest secret accepted for HMAC-SHA256, per RFC 7518 §3.2.
_MINIMUM_SECRET_LENGTH = 32

_ALGORITHM = "HS256"


class JwtTokenService:
    """Issues and verifies signed, self-contained session tokens.

    Stateless by design (SDP §5): the panel keeps no session table, so the
    same token authenticates a browser and an automation client without either
    consulting shared state.
    """

    def __init__(self, clock: ClockPort, lifetime: timedelta, secret: str | None = None) -> None:
        """Initialize the service.

        Args:
            clock: Supplies issue and expiry times.
            lifetime: How long an issued token stays valid.
            secret: Signing secret; taken from ``$VAE_JWT_SECRET`` when omitted.

        Raises:
            RuntimeError: If no secret is configured, or the configured one is
                too short to sign with safely.
        """
        self._clock = clock
        self._lifetime = lifetime
        self._secret = secret or os.getenv(SECRET_ENV_VAR) or ""

        if not self._secret:
            raise RuntimeError(
                f"{SECRET_ENV_VAR} is not set; the operations panel cannot issue "
                f"session tokens without a signing secret"
            )
        if len(self._secret) < _MINIMUM_SECRET_LENGTH:
            raise RuntimeError(
                f"{SECRET_ENV_VAR} must be at least {_MINIMUM_SECRET_LENGTH} "
                f"characters for HMAC-SHA256"
            )

    def issue(self, user: AuthenticatedUser) -> tuple[str, Session]:
        """Issue a token for an authenticated operator.

        Args:
            user: The operator to issue for.

        Returns:
            The encoded token and the session it represents.
        """
        issued_at = self._clock.now()
        expires_at = issued_at + self._lifetime
        session = Session(user=user, issued_at=issued_at, expires_at=expires_at)

        token = jwt.encode(
            {
                "sub": user.username,
                "name": user.display_name,
                "authorizations": sorted(item.value for item in user.authorizations),
                "iat": int(issued_at.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            self._secret,
            algorithm=_ALGORITHM,
        )
        return token, session

    def verify(self, token: str) -> Session:
        """Decode and validate a token.

        Args:
            token: The encoded token.

        Returns:
            The session it carries.

        Raises:
            AuthenticationFailed: If the token is malformed, signed with
                another key, or expired.
        """
        try:
            # Expiry is checked against the injected clock rather than here:
            # two independent notions of "now" would disagree, and the caller
            # already rejects an expired session through Session.is_expired.
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed("Session token is not valid") from exc

        return Session(
            user=AuthenticatedUser(
                username=payload["sub"],
                display_name=payload.get("name", payload["sub"]),
                authorizations=frozenset(
                    Authorization(value) for value in payload.get("authorizations", [])
                ),
            ),
            issued_at=datetime.fromtimestamp(payload["iat"], tz=self._clock.now().tzinfo),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=self._clock.now().tzinfo),
        )
