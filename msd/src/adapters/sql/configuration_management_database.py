"""
Description: Configuration management database adapter running operator-configured SQL (EXT-IF-01).
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError

from msd.src.model.configuration_data import Platform, Project, SystemVersion
from msd.src.model.data_source import DataSourceConfiguration
from msd.src.model.version_inventory import SoftwareUnitVersion
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from shared.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef

#: Column names each query is expected to return, unless the source's
#: configuration overrides them.
_DEFAULT_COLUMNS: dict[str, dict[str, str]] = {
    "projects": {"name": "name"},
    "platforms": {"name": "name"},
    "versions": {"version": "version", "effective": "effective"},
    "software_units": {"name": "name", "version": "version", "source_name": "source_name"},
}


@lru_cache(maxsize=16)
def _engine_for(url: str) -> Engine:
    """Return a pooled engine for a connection URL.

    Adapters are built per request, so without this each request would open a
    new pool against the same database.
    """
    return create_engine(url, pool_pre_ping=True, future=True)


class SqlConfigurationManagementDatabase:
    """Reads project/platform/version information with SQL the operator supplies.

    The schema belongs to the customer's configuration management database, not
    to SaaG, so the four queries are configuration rather than code: this
    adapter knows *that* there are projects, platforms, versions and software
    units, and nothing about how they are stored. Pointing at a different
    database — or a differently-shaped one — is a source configuration edit.

    Queries live under the source's ``parameters``:

    ``queries.projects``
        Returns one row per project.
    ``queries.platforms``
        Returns one row per platform of ``:project``.
    ``queries.versions``
        Returns one row per system version of ``:project``/``:platform``,
        carrying a truthy ``effective`` column for the effective one.
    ``queries.software_units``
        Returns one row per software unit of ``:project``/``:platform``/
        ``:version``, optionally naming the repository that holds it.

    ``columns.<query>.<field>`` renames the column a query returns, for schemas
    that name things differently.
    """

    def __init__(
        self, configuration: DataSourceConfiguration, password: str | None = None
    ) -> None:
        """Initialize the adapter.

        Args:
            configuration: The database this instance serves; its
                ``connection_address`` is a SQLAlchemy URL.
            password: Resolved credential, injected into the URL. None leaves
                whatever the URL already carries.

        Raises:
            AcquisitionFailure: FORMAT_INCOMPATIBLE if the connection address
                is not a usable SQLAlchemy URL.
        """
        self._configuration = configuration
        self._parameters: dict[str, Any] = dict(configuration.parameters or {})
        self._url = self._build_url(password)

    @property
    def source_name(self) -> str:
        """Name of the configured source this instance serves."""
        return self._configuration.name

    def list_projects(self) -> list[Project]:
        """List the projects this database knows about (SRS MSD.10)."""
        rows = self._run("projects")
        columns = self._columns("projects")
        return [
            Project(
                ref=ProjectRef(str(row[columns["name"]])), source_name=self.source_name
            )
            for row in rows
        ]

    def list_platforms(self, project: ProjectRef) -> list[Platform]:
        """List a project's platforms (SRS MSD.11)."""
        rows = self._run("platforms", project=project.name)
        columns = self._columns("platforms")
        return [
            Platform(
                ref=PlatformRef(project, str(row[columns["name"]])),
                source_name=self.source_name,
            )
            for row in rows
        ]

    def list_system_versions(self, platform: PlatformRef) -> list[SystemVersion]:
        """List a platform's versions, marking the effective one (SRS MSD.12-13)."""
        rows = self._run(
            "versions", project=platform.project.name, platform=platform.name
        )
        columns = self._columns("versions")
        return [
            SystemVersion(
                ref=SystemVersionRef(platform, str(row[columns["version"]])),
                is_effective=bool(row[columns["effective"]]),
                source_name=self.source_name,
            )
            for row in rows
        ]

    def list_software_units(
        self, platform: PlatformRef, version: str
    ) -> list[SoftwareUnitVersion]:
        """List the software units defined for a system version (SRS MSD.14)."""
        rows = self._run(
            "software_units",
            project=platform.project.name,
            platform=platform.name,
            version=version,
        )
        columns = self._columns("software_units")
        return [
            SoftwareUnitVersion(
                unit_name=str(row[columns["name"]]),
                version=str(row[columns["version"]]),
                source_name=str(row.get(columns["source_name"]) or ""),
            )
            for row in rows
        ]

    def _build_url(self, password: str | None) -> str:
        try:
            url = make_url(self._configuration.connection_address)
        except Exception as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.FORMAT_INCOMPATIBLE,
                f"'{self.source_name}' has an unusable connection address",
                detail=str(exc),
            ) from exc

        credential = self._configuration.credential
        if credential is not None and credential.username:
            url = url.set(username=credential.username)
        if password:
            url = url.set(password=password)

        return url.render_as_string(hide_password=False)

    def _query(self, name: str) -> str:
        query = str(self._parameters.get("queries", {}).get(name, "")).strip()
        if not query:
            raise AcquisitionFailure(
                AcquisitionStatus.MISSING_DATA,
                f"'{self.source_name}' has no '{name}' query configured",
                detail="set parameters.queries on this data source",
            )
        return query

    def _columns(self, name: str) -> dict[str, str]:
        configured = self._parameters.get("columns", {}).get(name, {})
        return {**_DEFAULT_COLUMNS[name], **configured}

    def _run(self, name: str, **parameters: str) -> list[dict[str, Any]]:
        query = self._query(name)
        try:
            with _engine_for(self._url).connect() as connection:
                result = connection.execute(text(query), parameters)
                return [dict(row) for row in result.mappings()]
        except SQLAlchemyError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{self.source_name}' could not be queried for {name}",
                detail=str(exc.__cause__ or exc),
            ) from exc
        except KeyError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.FORMAT_INCOMPATIBLE,
                f"'{self.source_name}' returned no column {exc} for {name}",
            ) from exc
