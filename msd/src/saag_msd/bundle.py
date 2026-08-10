"""
Description: Component bundle publishing the MSD CSU's services into the framework.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from fastapi import APIRouter
from pelix.framework import BundleContext
from pelix.ipopo.decorators import (
    ComponentFactory,
    Instantiate,
    Invalidate,
    Property,
    Provides,
    Validate,
)

from saag_contracts.specs.api import ApiRouterProvider
from saag_contracts.specs.dto import (
    ModelSetupDataFileRecord,
    ProductionErrorRecord,
    ProductionOutcome,
    SourceProbeResult,
)
from saag_contracts.specs.model_setup_data import (
    CONTRACT_VERSION,
    AvailableSystemVersion,
    ModelSetupDataProvisioning,
)
from saag_contracts.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef
from saag_msd.api.provisioning import ModelSetupDataProvisioningService
from saag_msd.api.routes import build_router
from saag_msd.composition import build_container

#: Service property consumers may filter on to pin a contract version.
CONTRACT_VERSION_PROPERTY = "saag.contract.version"


@ComponentFactory("saag-msd-factory")
@Provides([ModelSetupDataProvisioning, ApiRouterProvider])
@Property("_contract_version", CONTRACT_VERSION_PROPERTY, CONTRACT_VERSION)
@Property("_database_url", "saag.env.database_url", None)
@Property("_workspace_dir", "saag.env.msd_workspace_dir", None)
@Property("_document_dir", "saag.env.msd_output_dir", None)
@Property("_rules_file", "saag.env.msd_rules_file", None)
@Property("_source_seed_file", "saag.env.msd_source_seed_file", None)
@Instantiate("saag-msd")
class MsdBundle:
    """MSD as one framework component (SDD §3.1.1, §2.5).

    Publishes the CSU's REST endpoints and its INT-IF-01 provisioning interface.
    Both are inbound adapters over one container, so the two protocols cannot
    disagree about what MSD currently is.

    The properties are the CSU's whole configuration surface: the framework host
    reads the environment once and supplies them, so nothing below this class
    reads it (SDD §2.5).
    """

    def __init__(self) -> None:
        self._container = None
        self._provisioning: ModelSetupDataProvisioningService | None = None
        self._router: APIRouter | None = None

    @Validate
    def _validate(self, context: BundleContext) -> None:
        """Wire MSD and publish its services."""
        self._container = build_container(
            database_url=self._database_url,
            workspace_dir=self._workspace_dir,
            document_dir=self._document_dir,
            rules_file=self._rules_file,
            source_seed_file=self._source_seed_file,
        )
        self._provisioning = ModelSetupDataProvisioningService(self._container)
        self._router = build_router(self._container)

    @Invalidate
    def _invalidate(self, context: BundleContext) -> None:
        """Drop MSD's wiring once its services are withdrawn."""
        self._container = None
        self._provisioning = None
        self._router = None

    def router(self) -> APIRouter:
        """Return MSD's router.

        Only reachable through the registered service, which exists solely while
        the component is valid, so the router is never absent here.
        """
        assert self._router is not None
        return self._router

    # ModelSetupDataProvisioning. Delegated rather than registered directly so
    # the component stays the single thing whose lifecycle the framework manages.

    def list_projects(self) -> list[str]:
        """List the projects available from the configuration source."""
        return self._service().list_projects()

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List a project's platforms."""
        return self._service().list_platforms(project)

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List a platform's system versions, marking the effective one."""
        return self._service().list_system_versions(platform)

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFileRecord]:
        """List the Model Setup Data files produced for a system version."""
        return self._service().list_model_setup_data_files(system_version)

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Run Model Setup Data production."""
        return self._service().produce(system_version, run_id)

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceProbeResult]:
        """Check every configured data source's accessibility."""
        return self._service().probe_sources(platform)

    def list_errors(self, platform: PlatformRef) -> list[ProductionErrorRecord]:
        """List the failures recorded for a platform."""
        return self._service().list_errors(platform)

    def _service(self) -> ModelSetupDataProvisioningService:
        assert self._provisioning is not None
        return self._provisioning
