"""
Description: INT-IF-01 service specification: the Model Setup Data provider's interface.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pelix.constants import Specification

from saag_contracts.specs.dto import (
    AvailableSystemVersion,
    ModelSetupDataFileRecord,
    ProductionErrorRecord,
    ProductionOutcome,
    SourceProbeResult,
)
from saag_contracts.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef

#: Registry name of the specification below (SDD Table 2, INT-IF-01).
MODEL_SETUP_DATA_PROVISIONING = "saag.int-if-01.model-setup-data-provisioning"

#: Contract version advertised by providers as the ``saag.contract.version``
#: service property, and pinnable by consumers through a service filter. Tracks
#: the Model Setup Data document schema version it hands over.
CONTRACT_VERSION = "1.0"


@Specification(MODEL_SETUP_DATA_PROVISIONING)
@runtime_checkable
class ModelSetupDataProvisioning(Protocol):
    """Everything the CSCI asks of Model Setup Data Generation (SDD §2.3).

    One provided interface with two consumers, which is why it lives here rather
    than in the providing CSU: CSM-01 selects and ingests produced files
    (INT-IF-01), while VAE-01 drives production and reports on it (SDD §2.2 step
    6). Neither consumer may depend on the provider's distribution, so both
    depend on this specification instead.

    All methods are synchronous and may block on external systems; the platform
    calls them off the event loop.
    """

    def list_projects(self) -> list[str]:
        """List the projects available from the configuration source.

        Returns:
            Project names (SRS MSD.10).

        Raises:
            AcquisitionFailure: If the configuration source cannot be read.
        """
        ...

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List a project's platforms.

        Args:
            project: Project to list under.

        Returns:
            Platform names (SRS MSD.11).

        Raises:
            AcquisitionFailure: If the configuration source cannot be read.
        """
        ...

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List a platform's system versions, marking the effective one.

        Args:
            platform: Platform to list under.

        Returns:
            One entry per version, at most one flagged effective
            (SRS MSD.12-13).

        Raises:
            AcquisitionFailure: If the configuration source cannot be read.
        """
        ...

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFileRecord]:
        """List the Model Setup Data files produced for a system version.

        Args:
            system_version: Scope to list for.

        Returns:
            One record per produced file, most recent first (SRS MSD.23).
        """
        ...

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Run Model Setup Data production.

        Blocking and long-running: acquires from every configured external
        source, validates, and assembles one document (SRS MSD.1, 21-23).
        Failures recorded along the way are returned rather than raised, so a
        partially failed run is still reportable.

        Args:
            system_version: Scope to produce for.
            run_id: Identifier to record the run under; the caller owns it so it
                can correlate its own operation record with the provider's.

        Returns:
            What the run produced, including everything it recorded as failed.
        """
        ...

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceProbeResult]:
        """Check every configured data source's accessibility (SRS MSD.2-5).

        Args:
            platform: Scope for sources whose probe needs one; None probes those
                with a placeholder scope.

        Returns:
            One result per configured source. A source that cannot be reached is
            reported unreachable, never omitted.
        """
        ...

    def list_errors(self, platform: PlatformRef) -> list[ProductionErrorRecord]:
        """List the failures recorded for a platform (SRS MSD.22).

        Args:
            platform: Scope to list for.

        Returns:
            Recorded failures, most recent first.
        """
        ...
