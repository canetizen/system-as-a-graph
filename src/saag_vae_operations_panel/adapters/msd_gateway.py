"""
Description: Drives Model Setup Data Generation over the provisioning service (INT-IF-01).
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Callable

from saag_contracts.specs.dto import ProductionErrorRecord, SourceProbeResult
from saag_contracts.specs.model_setup_data import ModelSetupDataProvisioning
from saag_contracts.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef
from saag_vae_operations_panel.model.production_job import (
    AvailableSystemVersion,
    ModelSetupDataFile,
    ProductionError,
)
from saag_vae_operations_panel.model.source_status import Accessibility, SourceStatus
from saag_vae_operations_panel.ports.model_setup_data import ProductionOutcome


class ModelSetupDataUnavailable(RuntimeError):
    """Raised when Model Setup Data Generation is not part of this CSCI.

    Distinct from a failure of the interface: nothing went wrong, the CSU simply
    is not installed or is not currently running (SDD §2.3.1). The panel reports
    the capability as unavailable rather than reporting an error, and recovers on
    its own when the CSU comes back.
    """


class ServiceModelSetupDataGateway:
    """Implements the panel's port over the provisioning service.

    Holds a callable that resolves the service rather than the service itself.
    The framework replaces the injected reference when the provider is restarted,
    so a reference captured once would be a dead object after the first restart —
    the single most likely bug in a design where providers come and go.

    Also the panel's translation layer: the contract's records become the panel's
    own domain types here, which is what keeps the panel's use cases and their
    tests independent of the contract's shape.
    """

    def __init__(self, provisioning: Callable[[], ModelSetupDataProvisioning | None]) -> None:
        """Bind the gateway to a resolver for the provisioning service.

        Args:
            provisioning: Returns the currently registered service, or None when
                no provider is registered.
        """
        self._provisioning = provisioning

    def list_projects(self) -> list[str]:
        """List the projects the operator may select."""
        return self._service().list_projects()

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List a project's platforms."""
        return self._service().list_platforms(project)

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List a platform's system versions, marking the effective one."""
        return [
            AvailableSystemVersion(version=item.version, is_effective=item.is_effective)
            for item in self._service().list_system_versions(platform)
        ]

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFile]:
        """List the Model Setup Data files produced for a system version."""
        return [
            ModelSetupDataFile(
                run_id=record.run_id,
                file_path=record.file_path,
                produced_at=record.produced_at,
                entity_count=record.entity_count,
                relation_count=record.relation_count,
                failure_count=record.failure_count,
            )
            for record in self._service().list_model_setup_data_files(system_version)
        ]

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Run Model Setup Data production."""
        outcome = self._service().produce(system_version, run_id)
        return ProductionOutcome(
            run_id=outcome.run_id,
            succeeded=outcome.succeeded,
            file_path=outcome.file_path,
            entity_count=outcome.entity_count,
            relation_count=outcome.relation_count,
            errors=[_to_error(error) for error in outcome.errors],
        )

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceStatus]:
        """Check every configured data source's accessibility (SRS VAE-01.7)."""
        return [_to_status(result) for result in self._service().probe_sources(platform)]

    def list_errors(self, platform: PlatformRef) -> list[ProductionError]:
        """List the failures recorded for a platform (SRS VAE-01.8)."""
        return [_to_error(error) for error in self._service().list_errors(platform)]

    def _service(self) -> ModelSetupDataProvisioning:
        service = self._provisioning()
        if service is None:
            raise ModelSetupDataUnavailable(
                "Model Setup Data Generation is not available in this deployment"
            )
        return service


def _to_error(record: ProductionErrorRecord) -> ProductionError:
    return ProductionError(
        status=record.status,
        reason=record.reason,
        source_name=record.source_name,
        source_type=record.source_type,
        occurred_at=record.occurred_at,
        detail=record.detail,
    )


def _to_status(result: SourceProbeResult) -> SourceStatus:
    return SourceStatus(
        source_type=result.source_type,
        source_name=result.source_name,
        accessibility=(
            Accessibility.REACHABLE if result.reachable else Accessibility.UNREACHABLE
        ),
        checked_at=result.checked_at,
        detail=result.detail,
    )
