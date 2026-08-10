"""
Description: REST and SSE endpoints of the VAE-01 operations panel (SRS VAE-01.1-8).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from saag_contracts.types.identifiers import PlatformRef, ProjectRef, system_version
from saag_vae_operations_panel.adapters.msd_gateway import ModelSetupDataUnavailable
from saag_vae_operations_panel.api.schemas import (
    LoginRequest,
    ModelSetupDataFileResponse,
    ProductionErrorResponse,
    ProductionJobResponse,
    ScopeSelectionRequest,
    SelectableScopeResponse,
    SelectFileRequest,
    SessionResponse,
    SourceStatusResponse,
    SourceStatusSnapshotResponse,
    SystemVersionOption,
    WorkingScopeResponse,
)
from saag_vae_operations_panel.composition import PanelContainer
from saag_vae_operations_panel.model.session import Authorization, Session
from saag_vae_operations_panel.model.source_status import SourceStatusSnapshot
from saag_vae_operations_panel.ports.directory_service import AuthenticationFailed
from saag_vae_operations_panel.use_cases.manage_model_setup_data import (
    UnknownModelSetupDataFile,
    UnknownProductionJob,
)
from saag_vae_operations_panel.use_cases.manage_session import NotAuthorized

#: Setting naming how often the accessibility stream re-probes, quoted in
#: documentation and in the deployment's configuration.
STREAM_INTERVAL_SETTING = "VAE_SOURCE_STREAM_SECONDS"

#: Seconds between accessibility probes when a deployment configures none.
#: Configurable because a slow external source should not be hammered.
DEFAULT_STREAM_SECONDS = 15.0

#: Seconds a client is asked to wait before retrying a capability that is not
#: currently part of this CSCI.
_RETRY_AFTER_SECONDS = 5


class _ReportsUnavailableCapability(APIRoute):
    """Turns an absent Model Setup Data provider into "not available".

    A capability whose CSU is not installed, or is momentarily restarting, has
    not failed — it is simply not part of this deployment right now (SDD §2.3.1).
    Reporting it as unavailable with a retry hint says exactly that, where a
    server error would blame the panel and a missing route would tell the browser
    the URL never existed.

    Applied as the router's route class so every endpoint answers the same way,
    rather than each one translating the same condition.
    """

    def get_route_handler(self) -> Callable[[StarletteRequest], Awaitable[Response]]:
        handle = super().get_route_handler()

        async def report_unavailable(request: StarletteRequest) -> Response:
            try:
                return await handle(request)
            except ModelSetupDataUnavailable as unavailable:
                raise HTTPException(
                    status_code=503,
                    detail=str(unavailable),
                    headers={"Retry-After": str(_RETRY_AFTER_SECONDS)},
                ) from unavailable

        return report_unavailable


def build_router(
    container: PanelContainer, *, stream_interval: float = DEFAULT_STREAM_SECONDS
) -> APIRouter:
    """Build the panel's inbound REST adapter over a wired container.

    The container is closed over rather than resolved per request: the router is
    created by the panel's component and lives exactly as long as it does.

    Args:
        container: The wired panel.
        stream_interval: Seconds between accessibility probes on the stream.

    Returns:
        The router to contribute to the CSCI's external API.
    """
    router = APIRouter(
            prefix="/vae/operations-panel",
            tags=["vae-operations-panel"],
            route_class=_ReportsUnavailableCapability,
        )


    @router.get("/health")
    def health():
        """Report that the operations panel is up."""
        return {"status": "ok", "csc": "vae", "csu": "operations_panel"}


    @router.post("/session", response_model=SessionResponse)
    def log_in(payload: LoginRequest):
        """Authenticate an operator against the directory service (SRS VAE-01.3).

        Raises:
            HTTPException: 401 when the credential is not accepted.
        """
        try:
            granted = container.session.log_in(payload.username, payload.password)
        except AuthenticationFailed as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        user = granted.session.user
        return SessionResponse(
            token=granted.token,
            username=user.username,
            display_name=user.display_name,
            authorizations=sorted(item.value for item in user.authorizations),
            expires_at=granted.session.expires_at,
        )


    @router.get("/session", response_model=SessionResponse)
    def current_session(authorization: str | None = Header(default=None)):
        """Report who the presented token belongs to."""
        session = _session(container, authorization, Authorization.VIEW)
        return SessionResponse(
            token="",
            username=session.user.username,
            display_name=session.user.display_name,
            authorizations=sorted(item.value for item in session.user.authorizations),
            expires_at=session.expires_at,
        )


    @router.get("/scope/projects", response_model=SelectableScopeResponse)
    def list_projects(authorization: str | None = Header(default=None)):
        """List the projects the operator may select (SRS VAE-01.4)."""
        _session(container, authorization, Authorization.VIEW)
        return SelectableScopeResponse(projects=container.session.list_projects().projects)


    @router.get("/scope/projects/{project}/platforms", response_model=SelectableScopeResponse)
    def list_platforms(
        project: str,
        authorization: str | None = Header(default=None),
    ):
        """List a project's platforms (SRS VAE-01.4)."""
        _session(container, authorization, Authorization.VIEW)
        return SelectableScopeResponse(platforms=container.session.list_platforms(project).platforms)


    @router.get(
        "/scope/projects/{project}/platforms/{platform}/versions",
        response_model=SelectableScopeResponse,
    )
    def list_versions(
        project: str,
        platform: str,
        authorization: str | None = Header(default=None),
    ):
        """List a platform's versions, marking the effective one (SRS VAE-01.4)."""
        _session(container, authorization, Authorization.VIEW)
        selectable = container.session.list_versions(project, platform)
        effective = selectable.effective_version

        return SelectableScopeResponse(
            versions=[
                SystemVersionOption(version=item.version, is_effective=item.is_effective)
                for item in selectable.versions
            ],
            effective_version=effective.version if effective else None,
        )


    @router.put("/scope", response_model=WorkingScopeResponse)
    def select_scope(
        payload: ScopeSelectionRequest,
        authorization: str | None = Header(default=None),
    ):
        """Record the project/platform/system version the operator selected."""
        session = _session(container, authorization, Authorization.VIEW)
        scope = container.session.select(
            session.user.username,
            system_version(payload.project, payload.platform, payload.system_version),
        )
        return _to_scope_response(scope)


    @router.get("/scope", response_model=WorkingScopeResponse)
    def current_scope(authorization: str | None = Header(default=None)):
        """Report the operator's current selection.

        Raises:
            HTTPException: 404 when the operator has selected nothing yet.
        """
        session = _session(container, authorization, Authorization.VIEW)
        scope = container.session.current(session.user.username)
        if scope is None:
            raise HTTPException(status_code=404, detail="No project/platform/version selected")
        return _to_scope_response(scope)


    @router.get("/model-setup-data", response_model=list[ModelSetupDataFileResponse])
    def list_files(authorization: str | None = Header(default=None)):
        """List the Model Setup Data files produced for the selection (SRS VAE-01.5)."""
        scope = _selected_scope(container, authorization)
        return [
            ModelSetupDataFileResponse(
                run_id=item.run_id,
                file_path=item.file_path,
                produced_at=item.produced_at,
                entity_count=item.entity_count,
                relation_count=item.relation_count,
                failure_count=item.failure_count,
            )
            for item in container.workflow.list_files(scope.system_version)
        ]


    @router.put("/model-setup-data/selected", response_model=WorkingScopeResponse)
    def select_file(
        payload: SelectFileRequest,
        authorization: str | None = Header(default=None),
    ):
        """Pick which produced file the operator will use (SRS VAE-01.5).

        Raises:
            HTTPException: 404 when no such file exists for the selection.
        """
        session = _session(container, authorization, Authorization.VIEW)
        try:
            container.workflow.select_file(session.user.username, payload.run_id)
        except UnknownModelSetupDataFile as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except UnknownProductionJob as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return _to_scope_response(container.session.current(session.user.username))


    @router.post("/production", response_model=ProductionJobResponse, status_code=202)
    def start_production(authorization: str | None = Header(default=None)):
        """Start Model Setup Data production for the selection (SRS VAE-01.6).

        Returns 202: the process has been accepted and is running, which is what
        makes the in-progress status observable.
        """
        session = _session(container, authorization, Authorization.PRODUCE_MODEL_SETUP_DATA)
        scope = container.session.current(session.user.username)
        if scope is None:
            raise HTTPException(status_code=409, detail="No project/platform/version selected")

        job = container.workflow.start_production(session.user.username, scope.system_version)
        return _to_job_response(container.workflow.status(job.job_id))


    @router.get("/production/{job_id}", response_model=ProductionJobResponse)
    def production_status(
        job_id: str,
        authorization: str | None = Header(default=None),
    ):
        """Report a production process's status (SRS VAE-01.6).

        Raises:
            HTTPException: 404 when the identifier is not recognized.
        """
        _session(container, authorization, Authorization.VIEW)
        try:
            return _to_job_response(container.workflow.status(job_id))
        except UnknownProductionJob as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


    @router.get("/production", response_model=list[ProductionJobResponse])
    def production_history(authorization: str | None = Header(default=None)):
        """List the production processes started for the selection."""
        scope = _selected_scope(container, authorization)
        return [
            _to_job_response(job) for job in container.workflow.history(scope.system_version)
        ]


    @router.get("/production-errors", response_model=list[ProductionErrorResponse])
    def production_errors(authorization: str | None = Header(default=None)):
        """List the failures recorded during production (SRS VAE-01.8)."""
        scope = _selected_scope(container, authorization)
        return [
            ProductionErrorResponse(
                status=error.status,
                reason=error.reason,
                source_name=error.source_name,
                source_type=error.source_type,
                occurred_at=error.occurred_at,
                detail=error.detail,
            )
            for error in container.workflow.errors(scope.system_version)
        ]


    @router.get("/source-status", response_model=SourceStatusSnapshotResponse)
    def source_status(
        project: str | None = Query(default=None),
        platform: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ):
        """Probe every configured source and report its accessibility (SRS VAE-01.7)."""
        _session(container, authorization, Authorization.VIEW)
        snapshot = container.workflow.check_sources(_platform(project, platform))
        return _to_snapshot_response(snapshot)


    @router.get("/source-status/stream")
    async def source_status_stream(
        request: Request,
        token: str = Query(...),
        project: str | None = Query(default=None),
        platform: str | None = Query(default=None),
    ):
        """Stream accessibility snapshots continuously (SRS VAE-01.7).

        Server-sent events, because "continuously display" means the panel pushes
        rather than the operator refreshing. The token arrives as a query parameter
        since ``EventSource`` cannot set headers; the CLI polls the plain endpoint
        above instead.
        """
        _authorize(container, token, Authorization.VIEW)

        return StreamingResponse(
            source_status_events(container, _platform(project, platform), request, stream_interval),
            media_type="text/event-stream",
        )

    return router


async def source_status_events(
    container: PanelContainer,
    platform: PlatformRef | None,
    request: Request | None = None,
    interval: float = DEFAULT_STREAM_SECONDS,
) -> AsyncIterator[str]:
    """Yield one server-sent event per accessibility probe.

    Stops as soon as the client goes away: each iteration probes every configured
    external source, so a stream nobody is reading would keep hitting them for
    nothing.

    Probing reaches external systems over the network, so it runs off the event
    loop; doing it inline would stall every other request served by this process
    for as long as the slowest source takes to answer.

    An absent Model Setup Data provider ends a frame, not the stream: the panel
    reports the capability as unavailable and keeps the connection open, so a
    stream held across a restart of that CSU recovers by itself instead of the
    operator having to reload.

    Args:
        container: The wired panel.
        platform: Scope for sources whose probe needs one.
        request: The client request, watched for disconnection; None never
            disconnects, which is what a direct consumer wants.
        interval: Seconds between probes.

    Yields:
        Formatted server-sent event frames.
    """
    while True:
        try:
            snapshot = await run_in_threadpool(container.workflow.check_sources, platform)
        except ModelSetupDataUnavailable as unavailable:
            yield f"event: unavailable\ndata: {json.dumps({'detail': str(unavailable)})}\n\n"
        else:
            payload = _to_snapshot_response(snapshot).model_dump(mode="json")
            yield f"data: {json.dumps(payload)}\n\n"

        if request is not None and await request.is_disconnected():
            return

        await asyncio.sleep(interval)


def _platform(project: str | None, platform: str | None) -> PlatformRef | None:
    if not project or not platform:
        return None
    return PlatformRef(ProjectRef(project), platform)


def _session(
    container: PanelContainer, authorization: str | None, required: Authorization
) -> Session:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="A session token is required")
    return _authorize(container, authorization.split(" ", 1)[1].strip(), required)


def _authorize(
    container: PanelContainer, token: str, required: Authorization
) -> Session:
    try:
        return container.session.authorize(token, required)
    except AuthenticationFailed as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _selected_scope(container: PanelContainer, authorization: str | None):
    session = _session(container, authorization, Authorization.VIEW)
    scope = container.session.current(session.user.username)
    if scope is None:
        raise HTTPException(status_code=409, detail="No project/platform/version selected")
    return scope


def _to_scope_response(scope) -> WorkingScopeResponse:
    return WorkingScopeResponse(
        project=scope.system_version.project.name,
        platform=scope.system_version.platform.name,
        system_version=scope.system_version.version,
        selected_is_effective=scope.selected_is_effective,
        selected_model_setup_data_run_id=scope.selected_model_setup_data_run_id,
    )


def _to_job_response(job) -> ProductionJobResponse:
    return ProductionJobResponse(
        job_id=job.job_id,
        status=job.status.value,
        project=job.system_version.project.name,
        platform=job.system_version.platform.name,
        system_version=job.system_version.version,
        started_by=job.started_by,
        started_at=job.started_at,
        finished_at=job.finished_at,
        run_id=job.run_id,
        file_path=job.file_path,
        failure_reason=job.failure_reason,
        entity_count=job.entity_count,
        relation_count=job.relation_count,
        error_count=job.error_count,
    )


def _to_snapshot_response(snapshot: SourceStatusSnapshot) -> SourceStatusSnapshotResponse:
    return SourceStatusSnapshotResponse(
        checked_at=snapshot.checked_at,
        all_reachable=snapshot.all_reachable,
        statuses=[
            SourceStatusResponse(
                source_type=status.source_type,
                source_name=status.source_name,
                accessibility=status.accessibility.value,
                checked_at=status.checked_at,
                detail=status.detail,
            )
            for status in snapshot.statuses
        ],
    )