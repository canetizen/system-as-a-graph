"""
Description: Component bundle publishing the VAE-01 CSU's services into the framework.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from fastapi import APIRouter
from pelix.framework import BundleContext
from pelix.ipopo.decorators import (
    ComponentFactory,
    Instantiate,
    Invalidate,
    Property,
    Provides,
    Requires,
    Validate,
)
from saag_contracts.specs.api import ApiRouterProvider
from saag_contracts.specs.model_setup_data import ModelSetupDataProvisioning
from saag_contracts.specs.tasks import JobQueue, TaskProvider

from saag_vae_operations_panel.adapters.job_queue import (
    PRODUCTION_TASK_NAME,
    to_request,
)
from saag_vae_operations_panel.api.routes import DEFAULT_STREAM_SECONDS, build_router
from saag_vae_operations_panel.composition import PanelContainer, build_panel_container


@ComponentFactory("saag-vae-01-factory")
@Provides([ApiRouterProvider, TaskProvider])
@Requires("_msd", ModelSetupDataProvisioning, optional=True)
@Requires("_queue", JobQueue)
@Property("_database_url", "saag.env.database_url", None)
@Property("_jwt_secret", "saag.env.vae_jwt_secret", None)
@Property("_session_minutes", "saag.env.vae_session_minutes", None)
@Property("_stream_seconds", "saag.env.vae_source_stream_seconds", None)
@Property("_ldap_url", "saag.env.ldap_url", None)
@Property("_ldap_bind_dn_template", "saag.env.ldap_bind_dn_template", None)
@Property("_ldap_group_search_base", "saag.env.ldap_group_search_base", None)
@Property("_ldap_service_bind_dn", "saag.env.ldap_service_bind_dn", None)
@Property("_ldap_service_password", "saag.env.ldap_service_password", None)
@Property("_ldap_group_authorizations", "saag.env.ldap_group_authorizations", None)
@Instantiate("saag-vae-01")
class VaeOperationsPanelBundle:
    """VAE-01 as one framework component (SDD §3.6.1, §2.5).

    Requires Model Setup Data Generation **optionally**, which is a deliberate
    choice rather than laxity. A mandatory requirement would invalidate the whole
    panel whenever that CSU restarted, withdrawing every endpoint including login
    and leaving a browser with URLs that had just existed. Optional keeps the
    panel serving and lets it report that one capability as unavailable, which is
    the truthful answer and recovers by itself (SDD §2.3.1).

    The deferral service is required outright: a panel that cannot start a
    production run has no purpose, and the host always provides one.
    """

    def __init__(self) -> None:
        self._msd: ModelSetupDataProvisioning | None = None
        self._queue: JobQueue | None = None
        self._container: PanelContainer | None = None
        self._router: APIRouter | None = None

    @Validate
    def _validate(self, context: BundleContext) -> None:
        """Wire the panel and publish its services."""
        assert self._queue is not None
        self._container = build_panel_container(
            # A resolver, not the service: the framework replaces the injected
            # reference when the provider restarts, and a captured one would be a
            # dead object from then on.
            provisioning=lambda: self._msd,
            queue=self._queue,
            database_url=self._database_url,
            jwt_secret=self._jwt_secret,
            session_minutes=self._session_minutes,
            ldap_url=self._ldap_url,
            ldap_bind_dn_template=self._ldap_bind_dn_template,
            ldap_group_search_base=self._ldap_group_search_base,
            ldap_service_bind_dn=self._ldap_service_bind_dn,
            ldap_service_password=self._ldap_service_password,
            ldap_group_authorizations=self._ldap_group_authorizations,
        )
        self._router = build_router(
            self._container, stream_interval=self._stream_interval()
        )

    @Invalidate
    def _invalidate(self, context: BundleContext) -> None:
        """Drop the panel's wiring once its services are withdrawn."""
        self._container = None
        self._router = None

    def router(self) -> APIRouter:
        """Return the panel's router.

        Only reachable through the registered service, which exists solely while
        the component is valid, so the router is never absent here.
        """
        assert self._router is not None
        return self._router

    def tasks(self) -> Mapping[str, Callable[..., Any]]:
        """Publish the panel's long-running operations for the worker."""
        return {PRODUCTION_TASK_NAME: self._run_production}

    def _run_production(
        self,
        job_id: str,
        project: str,
        platform: str,
        system_version: str,
        started_by: str,
    ) -> None:
        """Execute one queued production process.

        Called in whichever process holds the queue's worker, which has its own
        framework and therefore its own wiring of this CSU — the isolation the
        design wants, made explicit by the component rather than arising from a
        cached module-level object.

        Args:
            job_id: Job row to update.
            project: Project to produce for.
            platform: Platform to produce for.
            system_version: System version to produce for.
            started_by: Operator who started the process.
        """
        assert self._container is not None
        self._container.workflow.run(
            to_request(job_id, project, platform, system_version, started_by)
        )

    def _stream_interval(self) -> float:
        configured = self._stream_seconds
        return float(configured) if configured else DEFAULT_STREAM_SECONDS
