"""
Description: PostgreSQL-backed implementations of the operations panel's persistence ports.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from saag_contracts.types.identifiers import SystemVersionRef, system_version
from saag_vae_operations_panel.adapters.postgres.tables import (
    production_jobs,
    source_status_entries,
    working_scopes,
)
from saag_vae_operations_panel.model.production_job import JobStatus, ProductionJob
from saag_vae_operations_panel.model.source_status import (
    Accessibility,
    SourceStatus,
    SourceStatusSnapshot,
)
from saag_vae_operations_panel.model.working_scope import WorkingScope


class PostgresWorkingScopeRepository:
    """Stores each operator's selection in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def save(self, scope: WorkingScope) -> None:
        """Store an operator's selection, replacing their previous one."""
        with self._engine.begin() as connection:
            connection.execute(
                delete(working_scopes).where(working_scopes.c.username == scope.username)
            )
            connection.execute(
                insert(working_scopes).values(
                    username=scope.username,
                    project=scope.system_version.project.name,
                    platform=scope.system_version.platform.name,
                    system_version=scope.system_version.version,
                    selected_is_effective=scope.selected_is_effective,
                    selected_run_id=scope.selected_model_setup_data_run_id,
                )
            )

    def get(self, username: str) -> WorkingScope | None:
        """Fetch an operator's selection, or None when they have made none."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(working_scopes).where(working_scopes.c.username == username)
                )
                .mappings()
                .first()
            )

        if row is None:
            return None

        return WorkingScope(
            username=row["username"],
            system_version=system_version(
                row["project"], row["platform"], row["system_version"]
            ),
            selected_is_effective=bool(row["selected_is_effective"]),
            selected_model_setup_data_run_id=row["selected_run_id"],
        )


class PostgresProductionJobRepository:
    """Stores production processes in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def save(self, job: ProductionJob) -> None:
        """Store a job, replacing any with the same identifier."""
        with self._engine.begin() as connection:
            connection.execute(
                delete(production_jobs).where(production_jobs.c.job_id == job.job_id)
            )
            connection.execute(
                insert(production_jobs).values(
                    job_id=job.job_id,
                    project=job.system_version.project.name,
                    platform=job.system_version.platform.name,
                    system_version=job.system_version.version,
                    started_by=job.started_by,
                    status=job.status.value,
                    started_at=job.started_at,
                    finished_at=job.finished_at,
                    run_id=job.run_id,
                    file_path=job.file_path,
                    failure_reason=job.failure_reason,
                    entity_count=job.entity_count,
                    relation_count=job.relation_count,
                    error_count=job.error_count,
                )
            )

    def get(self, job_id: str) -> ProductionJob | None:
        """Fetch a job, or None when the identifier is unknown."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(production_jobs).where(production_jobs.c.job_id == job_id)
                )
                .mappings()
                .first()
            )
        return _to_job(row) if row else None

    def list_for(self, scope: SystemVersionRef) -> list[ProductionJob]:
        """Fetch the jobs started for a system version, newest first."""
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(production_jobs)
                    .where(
                        production_jobs.c.project == scope.project.name,
                        production_jobs.c.platform == scope.platform.name,
                        production_jobs.c.system_version == scope.version,
                    )
                    .order_by(production_jobs.c.started_at.desc())
                )
                .mappings()
                .all()
            )
        return [_to_job(row) for row in rows]


class PostgresSourceStatusRepository:
    """Stores accessibility snapshots in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def record(self, snapshot: SourceStatusSnapshot) -> None:
        """Store one snapshot, one row per probed source."""
        if not snapshot.statuses:
            return

        with self._engine.begin() as connection:
            for status in snapshot.statuses:
                connection.execute(
                    insert(source_status_entries).values(
                        checked_at=snapshot.checked_at,
                        source_type=status.source_type,
                        source_name=status.source_name,
                        accessibility=status.accessibility.value,
                        detail=status.detail,
                    )
                )

    def latest(self) -> SourceStatusSnapshot | None:
        """Fetch the most recent snapshot, or None when none was taken yet."""
        with self._engine.connect() as connection:
            newest = connection.execute(
                select(source_status_entries.c.checked_at)
                .order_by(source_status_entries.c.checked_at.desc())
                .limit(1)
            ).scalar()

            if newest is None:
                return None

            rows = (
                connection.execute(
                    select(source_status_entries)
                    .where(source_status_entries.c.checked_at == newest)
                    .order_by(source_status_entries.c.source_type, source_status_entries.c.source_name)
                )
                .mappings()
                .all()
            )

        return SourceStatusSnapshot(
            checked_at=newest,
            statuses=[
                SourceStatus(
                    source_type=row["source_type"],
                    source_name=row["source_name"],
                    accessibility=Accessibility(row["accessibility"]),
                    checked_at=row["checked_at"],
                    detail=row["detail"],
                )
                for row in rows
            ],
        )


def _to_job(row) -> ProductionJob:
    return ProductionJob(
        job_id=row["job_id"],
        system_version=system_version(
            row["project"], row["platform"], row["system_version"]
        ),
        started_by=row["started_by"],
        status=JobStatus(row["status"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        run_id=row["run_id"],
        file_path=row["file_path"],
        failure_reason=row["failure_reason"],
        entity_count=row["entity_count"],
        relation_count=row["relation_count"],
        error_count=row["error_count"],
    )
