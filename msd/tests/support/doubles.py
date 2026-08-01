"""
Description: In-test doubles for MSD's external sources, so fast tests need no servers.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

from dataclasses import dataclass, field

from msd.src.model.configuration_data import Platform, Project, SystemVersion
from msd.src.model.data_source import DataSourceConfiguration
from msd.src.model.network_topology import (
    Machine,
    NetworkComponent,
    NetworkTopology,
    TopologyAcquisitionMethod,
)
from msd.src.model.version_inventory import SoftwareUnitVersion
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from shared.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef

#: What the stand-in environment describes, restated in memory. Tests assert
#: against these rather than against a server's contents, so a change to the
#: stand-in data cannot silently rewrite what a test claims.
PROJECT = "skyline"
PLATFORM = "avionics"
EFFECTIVE_VERSION = "1.0.0"
OLDER_VERSION = "0.9.0"

UNITS: dict[str, list[tuple[str, str, str]]] = {
    EFFECTIVE_VERSION: [
        ("system_repo", "1.0.0", "bitbucket-a"),
        ("nav_app", "1.2.0", "bitbucket-a"),
        ("sensor_app", "2.0.1", ""),
        ("helper_lib", "1.0.0", ""),
    ],
    OLDER_VERSION: [
        ("system_repo", "1.0.0", "bitbucket-a"),
        ("nav_app", "1.1.0", "bitbucket-a"),
    ],
}

ARTIFACTS: dict[tuple[str, str], dict[str, str]] = {
    ("system_repo", "1.0.0"): {"path": "skyline/system_repo/1.0.0/system_repo-1.0.0.tar.gz"},
    ("nav_app", "1.2.0"): {"path": "skyline/nav_app/1.2.0/nav_app-1.2.0.tar.gz"},
    ("sensor_app", "2.0.1"): {"path": "skyline/sensor_app/2.0.1/sensor_app-2.0.1.tar.gz"},
    ("helper_lib", "1.0.0"): {"path": "skyline/helper_lib/1.0.0/helper_lib-1.0.0.jar"},
}


@dataclass
class FaultPolicy:
    """Per-source fault injection, so failure paths stay exercisable in tests.

    Keyed by source name so one repository can fail while the others keep
    delivering — the behaviour TC-MSD-04 requires.

    Attributes:
        faults: ``{source_name: {operation: status}}``.
    """

    faults: dict[str, dict[str, AcquisitionStatus]] = field(default_factory=dict)

    def check(self, source_name: str, operation: str) -> None:
        """Raise the configured failure for an operation, if any.

        Raises:
            AcquisitionFailure: When a fault is configured for this pair.
        """
        status = self.faults.get(source_name, {}).get(operation)
        if status is None:
            return
        raise AcquisitionFailure(
            status,
            f"Injected {status.value} on '{source_name}' during {operation}",
            detail="fault injection",
        )


class DoubleConfigurationManagementDatabase:
    """Answers project/platform/version questions from memory."""

    def __init__(
        self, configuration: DataSourceConfiguration, faults: FaultPolicy | None = None
    ) -> None:
        """Initialize the double."""
        self._configuration = configuration
        self._faults = faults or FaultPolicy()

    @property
    def source_name(self) -> str:
        """Name of the configured source this double serves."""
        return self._configuration.name

    def list_projects(self) -> list[Project]:
        """List the one project the double knows."""
        self._faults.check(self.source_name, "list_projects")
        return [Project(ref=ProjectRef(PROJECT), source_name=self.source_name)]

    def list_platforms(self, project: ProjectRef) -> list[Platform]:
        """List that project's one platform."""
        self._faults.check(self.source_name, "list_platforms")
        if project.name != PROJECT:
            return []
        return [
            Platform(ref=PlatformRef(project, PLATFORM), source_name=self.source_name)
        ]

    def list_system_versions(self, platform: PlatformRef) -> list[SystemVersion]:
        """List two versions, the newer one effective."""
        self._faults.check(self.source_name, "list_system_versions")
        if platform.name != PLATFORM:
            return []
        return [
            SystemVersion(
                ref=SystemVersionRef(platform, version),
                is_effective=version == EFFECTIVE_VERSION,
                source_name=self.source_name,
            )
            for version in (EFFECTIVE_VERSION, OLDER_VERSION)
        ]

    def list_software_units(
        self, platform: PlatformRef, version: str
    ) -> list[SoftwareUnitVersion]:
        """List the units defined for a version."""
        self._faults.check(self.source_name, "list_software_units")
        if platform.name != PLATFORM:
            return []
        return [
            SoftwareUnitVersion(unit_name=name, version=unit_version, source_name=source)
            for name, unit_version, source in UNITS.get(version, [])
        ]


class DoublePackageRepository:
    """Answers artifact lookups from memory."""

    def __init__(
        self, configuration: DataSourceConfiguration, faults: FaultPolicy | None = None
    ) -> None:
        """Initialize the double."""
        self._configuration = configuration
        self._faults = faults or FaultPolicy()

    @property
    def source_name(self) -> str:
        """Name of the configured registry this double serves."""
        return self._configuration.name

    def find_artifact(self, unit: SoftwareUnitVersion) -> dict[str, str] | None:
        """Return the artifact for a unit version, or None when there is none."""
        self._faults.check(self.source_name, "find_artifact")
        found = ARTIFACTS.get((unit.unit_name, unit.version))
        if found is None:
            return None
        return {"name": unit.unit_name, "version": unit.version, **found}


class DoubleNetworkTopologySource:
    """Reports a fixed topology, machines included."""

    def __init__(
        self, configuration: DataSourceConfiguration, faults: FaultPolicy | None = None
    ) -> None:
        """Initialize the double."""
        self._configuration = configuration
        self._faults = faults or FaultPolicy()

    @property
    def source_name(self) -> str:
        """Name of the configured source this double serves."""
        return self._configuration.name

    def fetch(self, platform: PlatformRef) -> NetworkTopology:
        """Return the topology for a platform, empty for any other."""
        self._faults.check(self.source_name, "fetch")
        if platform.name != PLATFORM:
            return NetworkTopology(
                method=TopologyAcquisitionMethod.AUTOMATIC, source_name=self.source_name
            )

        return NetworkTopology(
            method=TopologyAcquisitionMethod.AUTOMATIC,
            source_name=self.source_name,
            components=[
                NetworkComponent(
                    name="switch-core-1", component_type="switch", attributes={"vlan": "10"}
                ),
                NetworkComponent(
                    name="switch-core-2", component_type="switch", attributes={"vlan": "20"}
                ),
                NetworkComponent(
                    name="segment-mission",
                    component_type="segment",
                    attributes={"bandwidth_mbps": "1000"},
                ),
            ],
            machines=[
                Machine(name="console-1", attributes={"cpu_cores": "8", "rack": "A1"}),
                Machine(name="console-2", attributes={"cpu_cores": "4", "rack": "A2"}),
            ],
        )
