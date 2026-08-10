"""
Description: Retrieves project, platform, and version information from the CM databases (SRS MSD.9-13, 16).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field

from saag_contracts.errors.acquisition import (
    AcquisitionError,
    AcquisitionFailure,
    AcquisitionStatus,
)
from saag_contracts.types.identifiers import PlatformRef, ProjectRef
from saag_msd.model.configuration_data import (
    ConfigurationDataSet,
    Platform,
    Project,
    SystemVersion,
)
from saag_msd.model.data_source import DataSourceType
from saag_msd.model.version_inventory import SoftwareUnitVersion
from saag_msd.ports.external_sources import ConfigurationManagementDatabasePort
from saag_msd.use_cases._recording import RunRecorder


@dataclass
class AcquisitionOutcome:
    """Result of one configuration-data acquisition.

    Attributes:
        data: What was retrieved, merged across every reachable source.
        status: OK only when every configured source answered; otherwise the
            status of the first failure, which is what marks the acquisition
            process as errored (SRS MSD.16).
        errors: Failures recorded during the acquisition.
    """

    data: ConfigurationDataSet = field(default_factory=ConfigurationDataSet)
    status: AcquisitionStatus = AcquisitionStatus.OK
    errors: list[AcquisitionError] = field(default_factory=list)


class AcquireConfigurationDataUseCase:
    """Reads project/platform/version information across every configured CM database.

    Results from several sources are merged rather than raced: each source may
    know a different slice of the estate. A source that fails marks the whole
    acquisition with an error status while the reachable ones still contribute,
    so an operator sees both the data and the gap.
    """

    def __init__(self, sources: list[ConfigurationManagementDatabasePort]) -> None:
        """Initialize the use case.

        Args:
            sources: One adapter per configured configuration management
                database, in priority order.
        """
        self._sources = sources

    def list_projects(self, recorder: RunRecorder) -> AcquisitionOutcome:
        """Retrieve the known projects (SRS MSD.10).

        Args:
            recorder: Failure recorder for this run.

        Returns:
            The merged project list and the acquisition status.
        """
        outcome = AcquisitionOutcome()
        seen: set[str] = set()

        for source in self._sources:
            projects = self._call(source, outcome, recorder, source.list_projects)
            for project in projects or []:
                if project.ref.name not in seen:
                    seen.add(project.ref.name)
                    outcome.data.projects.append(project)

        return outcome

    def list_platforms(self, project: ProjectRef, recorder: RunRecorder) -> AcquisitionOutcome:
        """Retrieve a project's platforms (SRS MSD.11).

        Args:
            project: Project to list platforms for.
            recorder: Failure recorder for this run.

        Returns:
            The merged platform list and the acquisition status.
        """
        outcome = AcquisitionOutcome()
        seen: set[str] = set()

        for source in self._sources:
            platforms = self._call(
                source, outcome, recorder, source.list_platforms, project
            )
            for platform in platforms or []:
                if platform.ref.name not in seen:
                    seen.add(platform.ref.name)
                    outcome.data.platforms.append(platform)

        return outcome

    def list_system_versions(
        self, platform: PlatformRef, recorder: RunRecorder
    ) -> AcquisitionOutcome:
        """Retrieve a platform's system versions, marking the effective one (SRS MSD.12-13).

        Args:
            platform: Platform to list versions for.
            recorder: Failure recorder for this run.

        Returns:
            The merged version list and the acquisition status.
        """
        outcome = AcquisitionOutcome()
        seen: set[str] = set()

        for source in self._sources:
            versions = self._call(
                source, outcome, recorder, source.list_system_versions, platform
            )
            for version in versions or []:
                if version.ref.version not in seen:
                    seen.add(version.ref.version)
                    outcome.data.versions.append(version)

        return outcome

    def list_software_units(
        self, platform: PlatformRef, version: str, recorder: RunRecorder
    ) -> tuple[list[SoftwareUnitVersion], AcquisitionOutcome]:
        """Retrieve the software units defined for a system version (SRS MSD.14).

        Args:
            platform: Platform the version belongs to.
            version: System version number.
            recorder: Failure recorder for this run.

        Returns:
            The merged unit list and the acquisition outcome.
        """
        outcome = AcquisitionOutcome()
        units: list[SoftwareUnitVersion] = []
        seen: set[str] = set()

        for source in self._sources:
            found = self._call(
                source, outcome, recorder, source.list_software_units, platform, version
            )
            for unit in found or []:
                if unit.unit_name not in seen:
                    seen.add(unit.unit_name)
                    units.append(unit)

        return units, outcome

    def _call(self, source, outcome, recorder, method, *args):
        """Invoke one source, recording and absorbing an acquisition failure."""
        try:
            return method(*args)
        except AcquisitionFailure as failure:
            error = recorder.record_failure(
                failure,
                source_name=source.source_name,
                source_type=DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE.value,
            )
            outcome.errors.append(error)
            if outcome.status is AcquisitionStatus.OK:
                outcome.status = failure.status
            return None


# Re-exported so callers building an outcome by hand stay on one vocabulary.
__all__ = [
    "AcquireConfigurationDataUseCase",
    "AcquisitionOutcome",
    "ConfigurationDataSet",
    "Platform",
    "Project",
    "SystemVersion",
]
