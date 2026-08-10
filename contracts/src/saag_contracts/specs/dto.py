"""
Description: Data records exchanged across the CSCI's internal service specifications.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AvailableSystemVersion:
    """A system version a provider offers, with the effective one marked.

    Attributes:
        version: Version number as the configuration management database
            records it; kept as text, no ordering implied.
        is_effective: Whether this is the currently effective version
            (SRS MSD.13).
    """

    version: str
    is_effective: bool = False


@dataclass(frozen=True)
class ProductionErrorRecord:
    """One failure a provider recorded during an acquisition or production run.

    Mirrors ``errors.acquisition.AcquisitionError`` minus the platform, which
    the caller already knows because it scoped the query. ``status`` is the
    ``AcquisitionStatus`` value rather than the enum so the record stays
    comparable after crossing a process or storage boundary.

    Attributes:
        status: ``AcquisitionStatus`` value of the failure.
        reason: Cause, written for an operator.
        source_name: Configured source the failure is attributed to.
        source_type: Type of that source.
        occurred_at: When the failure was detected.
        detail: Extra context, such as a file path or exit code.
    """

    status: str
    reason: str
    source_name: str
    source_type: str
    occurred_at: datetime
    detail: str = ""


@dataclass(frozen=True)
class ModelSetupDataFileRecord:
    """A Model Setup Data file a consumer may select (SRS VAE-01.5, CSM-01.2).

    Attributes:
        run_id: Identifier the file is selected by.
        file_path: Where the document was written.
        produced_at: When it was produced.
        entity_count: Entities the document carries.
        relation_count: Relations the document carries.
        failure_count: Failures recorded during its production; a produced
            file may still carry recorded failures (SRS VAE-01.8).
    """

    run_id: str
    file_path: str
    produced_at: datetime
    entity_count: int = 0
    relation_count: int = 0
    failure_count: int = 0


@dataclass(frozen=True)
class ProductionOutcome:
    """What one Model Setup Data production run produced.

    Attributes:
        run_id: Provider's identifier for the run.
        succeeded: Whether a document was produced at all.
        file_path: Where it was written; empty when none was.
        entity_count: Entities in the document.
        relation_count: Relations in the document.
        errors: Failures recorded during the run. Non-empty is compatible with
            ``succeeded`` being true.
    """

    run_id: str
    succeeded: bool
    file_path: str = ""
    entity_count: int = 0
    relation_count: int = 0
    errors: tuple[ProductionErrorRecord, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SourceProbeResult:
    """One configured data source's accessibility at one moment (SRS VAE-01.7).

    Attributes:
        source_type: Type of the configured source.
        source_name: Name of the configured source.
        reachable: Whether it answered the probe.
        checked_at: When the probe ran.
        detail: Why it was unreachable; empty when reachable.
    """

    source_type: str
    source_name: str
    reachable: bool
    checked_at: datetime
    detail: str = ""
