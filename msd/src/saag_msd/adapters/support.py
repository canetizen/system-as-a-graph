"""
Description: Environment-backed credential resolver and system clock adapters.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from saag_contracts.errors.acquisition import AcquisitionFailure, AcquisitionStatus

from saag_msd.model.data_source import CredentialReference


class EnvCredentialResolver:
    """Resolves credential references from environment variables.

    Keeping secrets in the environment rather than in the source configuration
    row means an air-gapped deployment rotates a credential by editing its
    ``.env`` file, with no database change and nothing secret in the Model
    Setup Data file.
    """

    def resolve(self, reference: CredentialReference) -> str:
        """Resolve a credential reference to its secret.

        Args:
            reference: The stored reference.

        Returns:
            The secret value.

        Raises:
            AcquisitionFailure: AUTHORIZATION_ERROR when the referenced
                variable is unset or empty, since the connection cannot be
                authorized without it.
        """
        secret = os.getenv(reference.secret_env_var)
        if not secret:
            raise AcquisitionFailure(
                AcquisitionStatus.AUTHORIZATION_ERROR,
                f"Credential '{reference.secret_env_var}' is not set in the environment",
                detail=f"username={reference.username}",
            )
        return secret


class SystemClock:
    """Returns the current UTC time."""

    def now(self) -> datetime:
        """Return the current time, timezone-aware in UTC."""
        return datetime.now(tz=UTC)


class FixedClock:
    """Returns a fixed time, so error times and file names are deterministic in tests."""

    def __init__(self, moment: datetime) -> None:
        """Initialize the clock.

        Args:
            moment: The time every call returns.
        """
        self._moment = moment

    def now(self) -> datetime:
        """Return the configured time."""
        return self._moment
