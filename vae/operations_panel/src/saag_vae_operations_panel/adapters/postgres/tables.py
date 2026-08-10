"""
Description: SQLAlchemy tables backing the operations panel's own state.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine

metadata = MetaData()

#: Each operator's current project/platform/version and selected file
#: (SRS VAE-01.4-5). Keyed by operator, since two may work on different
#: platforms simultaneously.
working_scopes = Table(
    "vae01_working_scope",
    metadata,
    Column("username", String(128), primary_key=True),
    Column("project", String(128), nullable=False),
    Column("platform", String(128), nullable=False),
    Column("system_version", String(64), nullable=False),
    Column("selected_is_effective", Boolean, nullable=False, default=False),
    Column("selected_run_id", String(64), nullable=False, default=""),
)

#: Model Setup Data production processes and their status (SRS VAE-01.6).
#: Persisted rather than held in memory so a restart does not lose the state
#: of a process an operator is watching.
production_jobs = Table(
    "vae01_production_job",
    metadata,
    Column("job_id", String(64), primary_key=True),
    Column("project", String(128), nullable=False),
    Column("platform", String(128), nullable=False),
    Column("system_version", String(64), nullable=False),
    Column("started_by", String(128), nullable=False),
    Column("status", String(32), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("run_id", String(64), nullable=False, default=""),
    Column("file_path", Text, nullable=False, default=""),
    Column("failure_reason", Text, nullable=False, default=""),
    Column("entity_count", Integer, nullable=False, default=0),
    Column("relation_count", Integer, nullable=False, default=0),
    Column("error_count", Integer, nullable=False, default=0),
)

#: One row per probed source per snapshot, so accessibility is traceable over
#: time and not merely visible right now (SRS VAE-01.7).
source_status_entries = Table(
    "vae01_source_status",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("checked_at", DateTime(timezone=True), nullable=False, index=True),
    Column("source_type", String(64), nullable=False),
    Column("source_name", String(128), nullable=False),
    Column("accessibility", String(32), nullable=False),
    Column("detail", Text, nullable=False, default=""),
)


def create_schema(engine: Engine) -> None:
    """Create the panel's tables if they do not exist.

    Args:
        engine: Engine to create the tables through.
    """
    metadata.create_all(engine)


def build_engine(url: str) -> Engine:
    """Build a pooled engine for this CSU's metadata store.

    Duplicated rather than shared with the other CSUs deliberately: four lines of
    connection setup are a smaller cost than a distribution every CSU depends on,
    which would tie their releases together for nothing (SDD §2.5).

    Args:
        url: SQLAlchemy-style connection URL.

    Returns:
        The engine, with liveness checks on checkout so a connection dropped by
        the database is replaced rather than raising on first use.
    """
    return create_engine(url, pool_pre_ping=True, future=True)
