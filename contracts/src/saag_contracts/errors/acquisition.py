"""
Description: Common data-acquisition status and error record shared by every ingesting CSC.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from saag_contracts.types.identifiers import PlatformRef


class AcquisitionStatus(str, Enum):
    """Outcome of a single data-acquisition or validation step.

    SDD §1 decision 5 requires every acquisition path in the CSCI to report
    failures through one vocabulary instead of inventing its own, so this enum
    is shared rather than owned by any single CSC.
    """

    OK = "ok"
    MISSING_DATA = "missing_data"
    ACCESS_ERROR = "access_error"
    AUTHORIZATION_ERROR = "authorization_error"
    INTEGRITY_ERROR = "integrity_error"
    FORMAT_INCOMPATIBLE = "format_incompatible"

    @property
    def is_failure(self) -> bool:
        """Whether this status represents a failed acquisition."""
        return self is not AcquisitionStatus.OK


@dataclass(frozen=True)
class AcquisitionError:
    """A recorded acquisition or validation failure.

    Carries the full attribute set SRS MSD.22 demands — reason, source name,
    source type, project/platform association, and error time — so a failure is
    always attributable to a specific configured source without consulting logs.

    Attributes:
        status: Which failure occurred.
        reason: Human-readable cause, written for an operator, not a developer.
        source_name: Name of the configured data source that failed.
        source_type: Type of that data source (e.g. "source_repository").
        platform: Project/platform the failing acquisition was scoped to.
        occurred_at: When the failure was detected.
        detail: Optional extra context (file path, unit name, exit code).

    Raises:
        ValueError: If constructed with AcquisitionStatus.OK, which is not a
            failure and therefore must not produce an error record.
    """

    status: AcquisitionStatus
    reason: str
    source_name: str
    source_type: str
    platform: PlatformRef
    occurred_at: datetime
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.status.is_failure:
            raise ValueError("AcquisitionError requires a failure status")


class AcquisitionFailure(Exception):
    """Raised by an adapter when a source cannot be read.

    Adapters know *what* went wrong but not the project/platform scope of the
    run, so they raise this and the use case turns it into a fully-attributed
    AcquisitionError. This keeps the error vocabulary in one place while
    leaving scope knowledge in the application layer.

    Attributes:
        status: Which failure occurred.
        reason: Human-readable cause.
        detail: Optional extra context.
    """

    def __init__(self, status: AcquisitionStatus, reason: str, detail: str = "") -> None:
        if not status.is_failure:
            raise ValueError("AcquisitionFailure requires a failure status")
        super().__init__(reason)
        self.status = status
        self.reason = reason
        self.detail = detail
