"""
Description: Small outbound ports for credential resolution and time.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from saag_msd.model.data_source import CredentialReference


@runtime_checkable
class CredentialResolverPort(Protocol):
    """Turns a stored credential reference into a usable secret.

    Secrets are never persisted with the source configuration; only the name of
    the variable holding them is. Resolution happens at connection time so a
    rotated secret takes effect without editing stored configuration.
    """

    def resolve(self, reference: CredentialReference) -> str:
        """Resolve a credential reference to its secret.

        Args:
            reference: The stored reference.

        Returns:
            The secret value.

        Raises:
            AcquisitionFailure: With AUTHORIZATION_ERROR when the referenced
                variable is unset, since the connection cannot be authorized.
        """
        ...


@runtime_checkable
class ClockPort(Protocol):
    """Supplies the current time.

    Error records carry an error time (SRS MSD.22) and documents carry a
    production time, both of which must be deterministic under test.
    """

    def now(self) -> datetime:
        """Return the current time."""
        ...
