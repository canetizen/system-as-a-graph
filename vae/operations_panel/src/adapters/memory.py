"""
Description: In-memory persistence adapters for the panel, used without a database and in tests.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from copy import deepcopy

from shared.types.identifiers import SystemVersionRef
from vae.operations_panel.src.model.production_job import ProductionJob
from vae.operations_panel.src.model.source_status import SourceStatusSnapshot
from vae.operations_panel.src.model.working_scope import WorkingScope


class InMemoryWorkingScopeRepository:
    """Keeps each operator's selection in process memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._items: dict[str, WorkingScope] = {}

    def save(self, scope: WorkingScope) -> None:
        """Store an operator's selection, replacing their previous one."""
        self._items[scope.username] = scope

    def get(self, username: str) -> WorkingScope | None:
        """Fetch an operator's selection, or None when they have made none."""
        return self._items.get(username)


class InMemoryProductionJobRepository:
    """Keeps production processes in process memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._items: dict[str, ProductionJob] = {}

    def save(self, job: ProductionJob) -> None:
        """Store a job, replacing any with the same identifier."""
        self._items[job.job_id] = deepcopy(job)

    def get(self, job_id: str) -> ProductionJob | None:
        """Fetch a job, or None when the identifier is unknown."""
        found = self._items.get(job_id)
        return deepcopy(found) if found else None

    def list_for(self, system_version: SystemVersionRef) -> list[ProductionJob]:
        """Fetch the jobs started for a system version, newest first."""
        return sorted(
            (
                deepcopy(job)
                for job in self._items.values()
                if _scope_key(job.system_version) == _scope_key(system_version)
            ),
            key=lambda job: job.started_at,
            reverse=True,
        )


class InMemorySourceStatusRepository:
    """Keeps accessibility snapshots in process memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._items: list[SourceStatusSnapshot] = []

    def record(self, snapshot: SourceStatusSnapshot) -> None:
        """Store one snapshot."""
        self._items.append(snapshot)

    def latest(self) -> SourceStatusSnapshot | None:
        """Fetch the most recent snapshot, or None when none was taken yet."""
        return self._items[-1] if self._items else None


def _scope_key(system_version: SystemVersionRef) -> tuple[str, str, str]:
    return (
        system_version.project.name,
        system_version.platform.name,
        system_version.version,
    )
