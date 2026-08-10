"""
Description: REST endpoints exposing the MSD use cases.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from saag_contracts.errors.acquisition import AcquisitionError, AcquisitionStatus
from saag_contracts.types.identifiers import (
    PlatformRef,
    ProjectRef,
    SystemVersionRef,
    system_version,
)

from saag_msd.adapters.support import SystemClock
from saag_msd.api.schemas import (
    AcquisitionResponse,
    AddCandidateRequest,
    DataSourceModel,
    DocumentRecordModel,
    ErrorModel,
    InventoryResponse,
    ManualTopologyRequest,
    NetworkComponentModel,
    PlatformModel,
    ProduceRequest,
    ProductionResponse,
    ProjectModel,
    RecordInventoryRequest,
    ScopeModel,
    SoftwareUnitModel,
    SystemVersionModel,
    TopologyResponse,
)
from saag_msd.composition import Container
from saag_msd.model.data_source import (
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from saag_msd.model.network_topology import NetworkComponent, NetworkTopology
from saag_msd.model.version_inventory import (
    SoftwareUnitVersion,
    SoftwareUnitVersionInventory,
)
from saag_msd.use_cases._recording import RunRecorder
from saag_msd.use_cases.acquire_configuration_data import AcquisitionOutcome

#: Placeholder scope for acquisitions that run before a project is known, so a
#: failure recorded during project discovery is still attributable.
_UNKNOWN = "unknown"


def build_router(container: Container) -> APIRouter:
    """Build MSD's inbound REST adapter over a wired container.

    The container is closed over rather than resolved per request: the router
    is created by MSD's component and lives exactly as long as it does, so no
    endpoint can outlive the object graph behind it.

    Args:
        container: MSD's wired object graph.

    Returns:
        The router to contribute to the CSCI's external API.
    """
    router = APIRouter(prefix="/msd", tags=["msd"])


    @router.get("/health")
    def health():
        """Report that the MSD service is up."""
        return {"status": "ok", "csc": "msd"}


    @router.get("/data-sources", response_model=list[DataSourceModel])
    def list_data_sources():
        """List every configured external data source (SRS MSD.2-5, 8)."""
        return [_to_source_model(item) for item in container.data_sources.list_all()]


    @router.post("/data-sources", response_model=DataSourceModel, status_code=201)
    def configure_data_source(
        payload: DataSourceModel
    ):
        """Save a data source configuration, replacing one with the same key."""
        saved = container.data_sources.configure(
            DataSourceConfiguration(
                source_type=payload.source_type,
                name=payload.name,
                access_method=payload.access_method,
                connection_address=payload.connection_address,
                credential=(
                    CredentialReference(
                        username=payload.credential.username,
                        secret_env_var=payload.credential.secret_env_var,
                    )
                    if payload.credential
                    else None
                ),
                priority=payload.priority,
            )
        )
        return _to_source_model(saved)


    @router.delete("/data-sources/{source_type}/{name}", status_code=204)
    def delete_data_source(
        source_type: DataSourceType, name: str
    ):
        """Delete a data source configuration.

        Raises:
            HTTPException: 404 when no such configuration exists.
        """
        if not container.data_sources.remove(source_type, name):
            raise HTTPException(status_code=404, detail=f"No such data source: {name}")


    @router.get("/projects", response_model=AcquisitionResponse)
    def list_projects():
        """Retrieve the known projects from every configured CM database (SRS MSD.10)."""
        recorder = _recorder(container, PlatformRef(ProjectRef(_UNKNOWN), _UNKNOWN))
        outcome = container.configuration_data().list_projects(recorder)
        return AcquisitionResponse(
            status=outcome.status,
            projects=[
                ProjectModel(name=item.ref.name, source_name=item.source_name)
                for item in outcome.data.projects
            ],
            errors=[_to_error_model(error) for error in outcome.errors],
        )


    @router.get("/projects/{project}/platforms", response_model=AcquisitionResponse)
    def list_platforms(project: str):
        """Retrieve a project's platforms (SRS MSD.11)."""
        project_ref = ProjectRef(project)
        recorder = _recorder(container, PlatformRef(project_ref, _UNKNOWN))
        outcome = container.configuration_data().list_platforms(project_ref, recorder)
        return AcquisitionResponse(
            status=outcome.status,
            platforms=[
                PlatformModel(name=item.ref.name, source_name=item.source_name)
                for item in outcome.data.platforms
            ],
            errors=[_to_error_model(error) for error in outcome.errors],
        )


    @router.get(
        "/projects/{project}/platforms/{platform}/versions", response_model=AcquisitionResponse
    )
    def list_system_versions(
        project: str, platform: str
    ):
        """Retrieve a platform's system versions, marking the effective one (SRS MSD.12-13)."""
        platform_ref = PlatformRef(ProjectRef(project), platform)
        recorder = _recorder(container, platform_ref)
        outcome = container.configuration_data().list_system_versions(platform_ref, recorder)
        return AcquisitionResponse(
            status=outcome.status,
            versions=[
                SystemVersionModel(
                    version=item.ref.version,
                    is_effective=item.is_effective,
                    source_name=item.source_name,
                )
                for item in outcome.data.versions
            ],
            errors=[_to_error_model(error) for error in outcome.errors],
        )


    @router.post("/version-inventory", response_model=InventoryResponse)
    def record_inventory(
        payload: RecordInventoryRequest
    ):
        """Record the baseline Software Unit Version Inventory (SRS MSD.14)."""
        scope = _scope(payload.scope)
        recorder = _recorder(container, scope.platform)

        units, outcome = container.configuration_data().list_software_units(
            scope.platform, scope.version, recorder
        )
        inventory = container.inventory.record(scope, units)
        return _to_inventory_response(payload.scope, inventory, outcome)


    @router.post("/version-inventory/candidate", response_model=InventoryResponse)
    def add_candidate(payload: AddCandidateRequest):
        """Add a candidate version alongside the defined versions (SRS MSD.15)."""
        scope = _scope(payload.scope)
        inventory = container.inventory.add_candidate(
            scope,
            SoftwareUnitVersion(
                unit_name=payload.unit.unit_name,
                version=payload.unit.version,
                source_name=payload.unit.source_name,
                is_candidate=True,
            ),
        )
        return _to_inventory_response(payload.scope, inventory)


    @router.get("/version-inventory", response_model=InventoryResponse)
    def get_inventory(
        project: str = Query(...),
        platform: str = Query(...),
        version: str = Query(...),
    ):
        """Fetch the recorded inventory for a system version.

        Raises:
            HTTPException: 404 when nothing has been recorded for the scope.
        """
        scope_model = ScopeModel(project=project, platform=platform, system_version=version)
        inventory = container.inventory.get(_scope(scope_model))
        if inventory is None:
            raise HTTPException(status_code=404, detail="No inventory recorded for this scope")
        return _to_inventory_response(scope_model, inventory)


    @router.get("/network-topology", response_model=TopologyResponse)
    def acquire_topology(
        project: str = Query(...),
        platform: str = Query(...),
    ):
        """Acquire the network topology automatically (SRS MSD.6).

        Raises:
            HTTPException: 404 when no configured source supplied a topology.
        """
        platform_ref = PlatformRef(ProjectRef(project), platform)
        recorder = _recorder(container, platform_ref)
        topology = container.topology().acquire(platform_ref, recorder)
        if topology is None:
            raise HTTPException(
                status_code=404, detail="No configured source supplied a network topology"
            )
        return _to_topology_response(topology)


    @router.post("/network-topology/manual", response_model=TopologyResponse)
    def enter_topology(
        payload: ManualTopologyRequest
    ):
        """Record a manually entered network topology (SRS MSD.7)."""
        topology = container.topology().enter_manually(
            PlatformRef(ProjectRef(payload.project), payload.platform),
            [
                NetworkComponent(
                    name=component.name,
                    component_type=component.component_type,
                    attributes=component.attributes,
                )
                for component in payload.components
            ],
        )
        return _to_topology_response(topology)


    @router.post("/model-setup-data", response_model=ProductionResponse)
    def produce_model_setup_data(
        payload: ProduceRequest
    ):
        """Produce the Model Setup Data file for a system version (SRS MSD.21-23)."""
        result = container.production().produce(_scope(payload.scope), run_id=uuid4().hex)

        return ProductionResponse(
            run_id=result.run_id,
            succeeded=result.succeeded,
            file_path=result.file_path,
            entity_count=len(result.document.entities) if result.document else 0,
            relation_count=len(result.document.relations) if result.document else 0,
            excluded_units=result.excluded_units,
            errors=[_to_error_model(error) for error in result.errors],
        )


    @router.get("/model-setup-data", response_model=list[DocumentRecordModel])
    def list_model_setup_data(
        project: str = Query(...),
        platform: str = Query(...),
        version: str = Query(...),
    ):
        """List the Model Setup Data files produced for a system version."""
        scope_model = ScopeModel(project=project, platform=platform, system_version=version)
        return [
            DocumentRecordModel(
                run_id=record.run_id,
                scope=scope_model,
                file_path=record.file_path,
                produced_at=record.produced_at,
                entity_count=record.entity_count,
                relation_count=record.relation_count,
                failure_count=record.failure_count,
            )
            for record in container.documents.list_for(_scope(scope_model))
        ]


    @router.get("/model-setup-data/{run_id}")
    def get_model_setup_data(run_id: str):
        """Return a produced Model Setup Data document (INT-IF-01).

        Raises:
            HTTPException: 404 when no document was produced under that run id.
        """
        document = container.documents.load(run_id)
        if document is None:
            raise HTTPException(status_code=404, detail=f"No document for run '{run_id}'")
        return document


    @router.get("/errors", response_model=list[ErrorModel])
    def list_errors(
        project: str = Query(...),
        platform: str = Query(...),
    ):
        """List the failures recorded for a platform (SRS MSD.16, 20, 22)."""
        platform_ref = PlatformRef(ProjectRef(project), platform)
        return [
            _to_error_model(error) for error in container.errors.list_for_platform(platform_ref)
        ]

    return router


def _scope(model: ScopeModel) -> SystemVersionRef:
    return system_version(model.project, model.platform, model.system_version)


def _recorder(container: Container, platform: PlatformRef) -> RunRecorder:
    return RunRecorder(
        run_id=uuid4().hex,
        platform=platform,
        errors=container.errors,
        clock=SystemClock(),
    )


def _to_source_model(configuration: DataSourceConfiguration) -> DataSourceModel:
    return DataSourceModel(
        source_type=configuration.source_type,
        name=configuration.name,
        access_method=configuration.access_method,
        connection_address=configuration.connection_address,
        credential=(
            {
                "username": configuration.credential.username,
                "secret_env_var": configuration.credential.secret_env_var,
            }
            if configuration.credential
            else None
        ),
        priority=configuration.priority,
    )


def _to_inventory_response(
    scope: ScopeModel,
    inventory: SoftwareUnitVersionInventory,
    outcome: AcquisitionOutcome | None = None,
) -> InventoryResponse:
    return InventoryResponse(
        scope=scope,
        status=outcome.status if outcome else AcquisitionStatus.OK,
        baseline=[_to_unit_model(entry) for entry in inventory.baseline],
        candidates=[_to_unit_model(entry) for entry in inventory.candidates],
        errors=[_to_error_model(error) for error in outcome.errors] if outcome else [],
    )


def _to_unit_model(entry: SoftwareUnitVersion) -> SoftwareUnitModel:
    return SoftwareUnitModel(
        unit_name=entry.unit_name,
        version=entry.version,
        source_name=entry.source_name,
        is_candidate=entry.is_candidate,
    )


def _to_topology_response(topology: NetworkTopology) -> TopologyResponse:
    return TopologyResponse(
        method=topology.method.value,
        source_name=topology.source_name,
        components=[
            NetworkComponentModel(
                name=component.name,
                component_type=component.component_type,
                attributes=component.attributes,
            )
            for component in topology.components
        ],
    )


def _to_error_model(error: AcquisitionError) -> ErrorModel:
    return ErrorModel(
        status=error.status,
        reason=error.reason,
        source_name=error.source_name,
        source_type=error.source_type,
        project=error.platform.project.name,
        platform=error.platform.name,
        occurred_at=error.occurred_at,
        detail=error.detail,
    )