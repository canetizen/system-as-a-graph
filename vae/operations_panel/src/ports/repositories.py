"""
Description: Outbound persistence and job-queue ports for the operations panel.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.types.identifiers import SystemVersionRef
from vae.operations_panel.src.model.production_job import (
    ProductionJob,
    ProductionJobRequest,
)
from vae.operations_panel.src.model.source_status import SourceStatusSnapshot
from vae.operations_panel.src.model.working_scope import WorkingScope


@runtime_checkable
class WorkingScopeRepository(Protocol):
    """Persists each operator's current selection (SRS VAE-01.4-5)."""

    def save(self, scope: WorkingScope) -> None:
        """Store an operator's selection, replacing their previous one."""
        ...

    def get(self, username: str) -> WorkingScope | None:
        """Fetch an operator's selection, or None when they have made none."""
        ...


@runtime_checkable
class ProductionJobRepository(Protocol):
    """Persists production processes so their status survives a restart."""

    def save(self, job: ProductionJob) -> None:
        """Store a job, replacing any with the same identifier."""
        ...

    def get(self, job_id: str) -> ProductionJob | None:
        """Fetch a job, or None when the identifier is unknown."""
        ...

    def list_for(self, system_version: SystemVersionRef) -> list[ProductionJob]:
        """Fetch the jobs started for a system version, newest first."""
        ...


@runtime_checkable
class SourceStatusRepository(Protocol):
    """Records accessibility snapshots so the status is traceable, not just live."""

    def record(self, snapshot: SourceStatusSnapshot) -> None:
        """Store one snapshot."""
        ...

    def latest(self) -> SourceStatusSnapshot | None:
        """Fetch the most recent snapshot, or None when none was taken yet."""
        ...


@runtime_checkable
class JobQueuePort(Protocol):
    """Runs production processes outside the request that started them.

    Without this the operator could never observe an "in progress" state, which
    VAE-01.6 requires as one of the three reportable statuses.
    """

    def enqueue(self, request: ProductionJobRequest) -> None:
        """Queue a production process for execution.

        Args:
            request: What to produce, and which job row to update.
        """
        ...
