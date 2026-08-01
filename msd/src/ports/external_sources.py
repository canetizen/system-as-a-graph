"""
Description: Outbound ports for the four external data sources MSD acquires from.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from msd.src.model.configuration_data import Platform, Project, SystemVersion
from msd.src.model.network_topology import NetworkTopology
from msd.src.model.source_files import SourceFileRecord
from msd.src.model.version_inventory import SoftwareUnitVersion
from shared.types.identifiers import PlatformRef, ProjectRef

# Every port below is *instance-scoped*: one adapter instance serves one
# configured data source. A method therefore never means "the source code
# repository" but "this repository", which is what lets two Bitbucket servers
# and a GitLab coexist behind the same port. All of them raise
# shared.errors.acquisition.AcquisitionFailure when their source cannot be read.


@runtime_checkable
class ConfigurationManagementDatabasePort(Protocol):
    """Reads project/platform/version information (EXT-IF-01, SRS MSD.10-13)."""

    @property
    def source_name(self) -> str:
        """Name of the configured source this instance serves."""
        ...

    def list_projects(self) -> list[Project]:
        """List the projects this source knows about.

        Returns:
            Projects, in source order.

        Raises:
            AcquisitionFailure: If the source is unreachable or malformed.
        """
        ...

    def list_platforms(self, project: ProjectRef) -> list[Platform]:
        """List the platforms belonging to a project.

        Args:
            project: Project to list platforms for.

        Returns:
            Platforms, in source order.

        Raises:
            AcquisitionFailure: If the source is unreachable or malformed.
        """
        ...

    def list_system_versions(self, platform: PlatformRef) -> list[SystemVersion]:
        """List the system versions belonging to a platform, marking the effective one.

        Args:
            platform: Platform to list versions for.

        Returns:
            System versions, with at most one marked effective (SRS MSD.13).

        Raises:
            AcquisitionFailure: If the source is unreachable or malformed.
        """
        ...

    def list_software_units(self, platform: PlatformRef, version: str) -> list[SoftwareUnitVersion]:
        """List the software units defined for a system version (SRS MSD.14).

        Args:
            platform: Platform the version belongs to.
            version: System version number.

        Returns:
            Software unit versions, carrying an explicit repository assignment
            when the source defines one.

        Raises:
            AcquisitionFailure: If the source is unreachable or malformed.
        """
        ...


@runtime_checkable
class SourceCodeRepositoryPort(Protocol):
    """Transfers software unit files (EXT-IF-02, SRS MSD.17-20)."""

    @property
    def source_name(self) -> str:
        """Name of the configured repository this instance serves."""
        ...

    def holds(self, unit: SoftwareUnitVersion) -> bool:
        """Whether this repository holds a given software unit version.

        Used by the router to pick a repository when the configuration
        management database assigns none. Must not raise for a simple miss.

        Args:
            unit: Software unit version to look for.

        Returns:
            True when this repository can supply the unit.
        """
        ...

    def transfer(self, unit: SoftwareUnitVersion) -> list[SourceFileRecord]:
        """Transfer a unit's files into local storage and record their metadata.

        Args:
            unit: Software unit version to transfer.

        Returns:
            One record per transferred file, carrying name, path,
            package/version, update time, and this repository's name.

        Raises:
            AcquisitionFailure: On access, authorization, or integrity errors.
        """
        ...

    def check_access(self) -> None:
        """Verify this repository can be reached.

        Exists separately from ``holds`` because that method must stay silent
        about a simple miss, which makes it useless as a reachability signal: a
        repository that refuses the credential and one that merely lacks the
        unit would look identical.

        Raises:
            AcquisitionFailure: On access, authorization, or integrity errors.
        """
        ...

    def local_tree(self, unit: SoftwareUnitVersion) -> Path:
        """Return the local root a unit was transferred into.

        Code generation runs against this directory, so it must be the
        transferred copy rather than anything the source still owns.

        Args:
            unit: Software unit version to locate.

        Returns:
            Local root path; valid only after a successful transfer.
        """
        ...


@runtime_checkable
class PackageRepositoryPort(Protocol):
    """Confirms package artifacts exist for inventory entries (EXT-IF-03, SRS MSD.4)."""

    @property
    def source_name(self) -> str:
        """Name of the configured package repository this instance serves."""
        ...

    def find_artifact(self, unit: SoftwareUnitVersion) -> dict[str, str] | None:
        """Look up the package artifact for a software unit version.

        Args:
            unit: Software unit version to look up.

        Returns:
            Artifact metadata, or None when this repository has no such
            artifact — which is a validation failure, not an access error.

        Raises:
            AcquisitionFailure: If the repository is unreachable or malformed.
        """
        ...


@runtime_checkable
class NetworkTopologySourcePort(Protocol):
    """Reads network topology data automatically (EXT-IF-04, SRS MSD.6)."""

    @property
    def source_name(self) -> str:
        """Name of the configured topology source this instance serves."""
        ...

    def fetch(self, platform: PlatformRef) -> NetworkTopology:
        """Fetch the topology for a platform.

        Args:
            platform: Platform to fetch topology for.

        Returns:
            The topology, with acquisition method AUTOMATIC.

        Raises:
            AcquisitionFailure: If the source is unreachable or malformed.
        """
        ...
