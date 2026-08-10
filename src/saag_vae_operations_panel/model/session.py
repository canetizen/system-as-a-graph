"""
Description: Authenticated operator and the authorizations a session carries (SRS VAE-01.3).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Authorization(str, Enum):
    """What an authenticated operator is allowed to do.

    VAE-01.3 grants access "within the scope of their authorizations", so
    authentication alone is never enough: every operation names the
    authorization it requires and the session is checked against it.
    """

    VIEW = "view"
    CONFIGURE_SOURCES = "configure_sources"
    PRODUCE_MODEL_SETUP_DATA = "produce_model_setup_data"


@dataclass(frozen=True)
class AuthenticatedUser:
    """An operator the directory service accepted.

    Attributes:
        username: Directory account name.
        display_name: Human-readable name for the UI.
        authorizations: What this operator may do.
    """

    username: str
    display_name: str
    authorizations: frozenset[Authorization] = field(default_factory=frozenset)

    def may(self, authorization: Authorization) -> bool:
        """Whether this operator holds an authorization.

        Args:
            authorization: The authorization to check.

        Returns:
            True when the operator holds it.
        """
        return authorization in self.authorizations


@dataclass(frozen=True)
class Session:
    """A granted session, as carried by the token issued at login.

    Attributes:
        user: The authenticated operator.
        issued_at: When the session began.
        expires_at: When the token stops being accepted.
    """

    user: AuthenticatedUser
    issued_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        """Whether the session has expired.

        Args:
            now: The current time.

        Returns:
            True when the session may no longer be used.
        """
        return now >= self.expires_at
