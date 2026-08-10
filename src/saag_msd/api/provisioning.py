"""
Description: Inbound adapter serving INT-IF-01 from MSD's wired container.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from uuid import uuid4

from saag_contracts.errors.acquisition import AcquisitionError, AcquisitionFailure
from saag_contracts.specs.dto import (
    AvailableSystemVersion,
    ModelSetupDataFileRecord,
    ProductionErrorRecord,
    ProductionOutcome,
    SourceProbeResult,
)
from saag_contracts.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef

from saag_msd.adapters.support import SystemClock
from saag_msd.composition import Container
from saag_msd.model.data_source import DataSourceType
from saag_msd.model.version_inventory import SoftwareUnitVersion
from saag_msd.use_cases._recording import RunRecorder

#: Placeholder used when a call needs a scope it has not been given, so a
#: failure recorded during project discovery is still attributable.
_UNKNOWN = "unknown"

#: Unit name a repository probe asks about. It is not expected to exist; the
#: point is to make the adapter touch its source, not to find anything.
_PROBE_UNIT = SoftwareUnitVersion(unit_name="__accessibility_probe__", version="0.0.0")


class ModelSetupDataProvisioningService:
    """Serves the Model Setup Data provisioning interface (SDD §2.3.1, INT-IF-01).

    An inbound adapter, peer to the REST router and differing only in protocol:
    it translates calls arriving over the component registry into MSD's use
    cases, and MSD's domain types into the contract's records. Consumers —
    CSM-01 ingesting produced files, VAE-01 driving production — therefore see
    published records and never MSD's internals.
    """

    def __init__(self, container: Container) -> None:
        """Bind the adapter to MSD's wiring.

        Args:
            container: MSD's wired object graph.
        """
        self._container = container

    def list_projects(self) -> list[str]:
        """List the projects available from the configuration source."""
        outcome = self._container.configuration_data().list_projects(
            self._recorder(PlatformRef(ProjectRef(_UNKNOWN), _UNKNOWN))
        )
        return [project.ref.name for project in outcome.data.projects]

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List a project's platforms."""
        outcome = self._container.configuration_data().list_platforms(
            project, self._recorder(PlatformRef(project, _UNKNOWN))
        )
        return [platform.ref.name for platform in outcome.data.platforms]

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List a platform's system versions, marking the effective one."""
        outcome = self._container.configuration_data().list_system_versions(
            platform, self._recorder(platform)
        )
        return [
            AvailableSystemVersion(
                version=version.ref.version, is_effective=version.is_effective
            )
            for version in outcome.data.versions
        ]

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFileRecord]:
        """List the Model Setup Data files produced for a system version."""
        return [
            ModelSetupDataFileRecord(
                run_id=record.run_id,
                file_path=record.file_path,
                produced_at=record.produced_at,
                entity_count=record.entity_count,
                relation_count=record.relation_count,
                failure_count=record.failure_count,
            )
            for record in self._container.documents.list_for(system_version)
        ]

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Run Model Setup Data production and report what it produced."""
        result = self._container.production().produce(system_version, run_id=run_id)
        return ProductionOutcome(
            run_id=result.run_id,
            succeeded=result.succeeded,
            file_path=result.file_path,
            entity_count=len(result.document.entities) if result.document else 0,
            relation_count=len(result.document.relations) if result.document else 0,
            errors=tuple(_to_error(error) for error in result.errors),
        )

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceProbeResult]:
        """Touch every configured source and report whether it answered.

        Each source type is probed with the cheapest call its adapter offers, so
        an unreachable address, a missing credential, or a malformed response all
        surface the same way an acquisition would have found them.

        Args:
            platform: Scope for sources whose probe needs one; None probes those
                with a placeholder scope.

        Returns:
            One result per configured source; an unreachable source is reported,
            never omitted.
        """
        scope = platform or PlatformRef(ProjectRef(_UNKNOWN), _UNKNOWN)
        checked_at = SystemClock().now()
        registry = self._container.registry()
        factory = self._container.factory

        results: list[SourceProbeResult] = []
        for configuration in registry.configurations:
            detail = ""
            try:
                adapter = factory.build(configuration)
                self._touch(configuration.source_type, adapter, scope)
            except AcquisitionFailure as failure:
                detail = failure.reason
            except KeyError:
                detail = (
                    f"No adapter registered for access method "
                    f"'{configuration.access_method.value}'"
                )

            results.append(
                SourceProbeResult(
                    source_type=configuration.source_type.value,
                    source_name=configuration.name,
                    reachable=not detail,
                    checked_at=checked_at,
                    detail=detail,
                )
            )

        return results

    def list_errors(self, platform: PlatformRef) -> list[ProductionErrorRecord]:
        """List the failures recorded for a platform (SRS MSD.22)."""
        return [
            _to_error(error) for error in self._container.errors.list_for_platform(platform)
        ]

    @staticmethod
    def _touch(source_type: DataSourceType, adapter, platform: PlatformRef) -> None:
        if source_type is DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE:
            adapter.list_projects()
        elif source_type is DataSourceType.SOURCE_REPOSITORY:
            adapter.check_access()
        elif source_type is DataSourceType.PACKAGE_REPOSITORY:
            adapter.find_artifact(_PROBE_UNIT)
        elif source_type is DataSourceType.NETWORK_TOPOLOGY:
            adapter.fetch(platform)

    def _recorder(self, platform: PlatformRef) -> RunRecorder:
        return RunRecorder(
            run_id=uuid4().hex,
            platform=platform,
            errors=self._container.errors,
            clock=SystemClock(),
        )


def _to_error(error: AcquisitionError) -> ProductionErrorRecord:
    return ProductionErrorRecord(
        status=error.status.value,
        reason=error.reason,
        source_name=error.source_name,
        source_type=error.source_type,
        occurred_at=error.occurred_at,
        detail=error.detail,
    )
