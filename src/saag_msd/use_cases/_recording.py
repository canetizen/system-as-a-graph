"""
Description: Single funnel turning adapter failures into attributed, recorded error entries.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from saag_contracts.errors.acquisition import (
    AcquisitionError,
    AcquisitionFailure,
    AcquisitionStatus,
)
from saag_contracts.types.identifiers import PlatformRef
from saag_msd.ports.repositories import AcquisitionErrorRepository
from saag_msd.ports.support import ClockPort


class RunRecorder:
    """Records every failure of one production run through one code path.

    SDD §1 decision 5 requires a single validation-and-error-recording pattern
    across the CSCI rather than each acquisition path inventing its own. This
    class is that pattern for MSD: adapters raise, the recorder attributes the
    failure to a source and a project/platform and stamps it with the error
    time (SRS MSD.22), and the caller decides whether to continue.
    """

    def __init__(
        self,
        run_id: str,
        platform: PlatformRef,
        errors: AcquisitionErrorRepository,
        clock: ClockPort,
    ) -> None:
        """Initialize the recorder.

        Args:
            run_id: Identifier of the production run being recorded.
            platform: Project/platform scope every failure is attributed to.
            errors: Repository failures are written to.
            clock: Supplies the error time.
        """
        self._run_id = run_id
        self._platform = platform
        self._errors = errors
        self._clock = clock
        self._recorded: list[AcquisitionError] = []

    @property
    def recorded(self) -> list[AcquisitionError]:
        """Failures recorded so far during this run."""
        return list(self._recorded)

    @property
    def has_failures(self) -> bool:
        """Whether anything failed during this run."""
        return bool(self._recorded)

    def record(self, error: AcquisitionError) -> AcquisitionError:
        """Record an already-built error entry.

        Args:
            error: The entry to record.

        Returns:
            The same entry, for convenience.
        """
        self._errors.record(self._run_id, error)
        self._recorded.append(error)
        return error

    def record_failure(
        self, failure: AcquisitionFailure, source_name: str, source_type: str
    ) -> AcquisitionError:
        """Attribute an adapter failure to a source and record it.

        Args:
            failure: The failure raised by an adapter.
            source_name: Configured source that failed.
            source_type: Type of that source.

        Returns:
            The recorded entry.
        """
        return self.record(
            AcquisitionError(
                status=failure.status,
                reason=failure.reason,
                source_name=source_name,
                source_type=source_type,
                platform=self._platform,
                occurred_at=self._clock.now(),
                detail=failure.detail,
            )
        )

    def record_missing(
        self, reason: str, source_name: str, source_type: str, detail: str = ""
    ) -> AcquisitionError:
        """Record a missing-data condition that no adapter raised.

        Used where absence is discovered by MSD's own checks — an unroutable
        unit, an unsatisfied mandatory file, a package with no artifact.

        Args:
            reason: What is missing.
            source_name: Source the absence is attributed to.
            source_type: Type of that source.
            detail: Optional extra context.

        Returns:
            The recorded entry.
        """
        return self.record(
            AcquisitionError(
                status=AcquisitionStatus.MISSING_DATA,
                reason=reason,
                source_name=source_name,
                source_type=source_type,
                platform=self._platform,
                occurred_at=self._clock.now(),
                detail=detail,
            )
        )
