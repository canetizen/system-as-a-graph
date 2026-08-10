"""
Description: Composition root wiring the operations panel to its adapters.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from saag_contracts.specs.model_setup_data import ModelSetupDataProvisioning
from saag_contracts.specs.tasks import JobQueue
from saag_vae_operations_panel.adapters.job_queue import DeferringJobQueue
from saag_vae_operations_panel.adapters.jwt_tokens import JwtTokenService
from saag_vae_operations_panel.adapters.ldap.directory_service import (
    LdapDirectoryService,
)
from saag_vae_operations_panel.adapters.memory import (
    InMemoryProductionJobRepository,
    InMemorySourceStatusRepository,
    InMemoryWorkingScopeRepository,
)
from saag_vae_operations_panel.adapters.msd_gateway import ServiceModelSetupDataGateway
from saag_vae_operations_panel.adapters.postgres.repositories import (
    PostgresProductionJobRepository,
    PostgresSourceStatusRepository,
    PostgresWorkingScopeRepository,
)
from saag_vae_operations_panel.adapters.postgres.tables import (
    build_engine,
    create_schema,
)
from saag_vae_operations_panel.adapters.support import SystemClock
from saag_vae_operations_panel.ports.directory_service import DirectoryServicePort
from saag_vae_operations_panel.ports.repositories import (
    ProductionJobRepository,
    SourceStatusRepository,
    WorkingScopeRepository,
)
from saag_vae_operations_panel.use_cases.manage_model_setup_data import (
    ModelSetupDataWorkflowUseCase,
)
from saag_vae_operations_panel.use_cases.manage_session import (
    SessionAndAuthenticationUseCase,
)

#: Session lifetime used when a deployment configures none.
DEFAULT_SESSION_MINUTES = 480


@dataclass
class PanelContainer:
    """The wired object graph the panel serves calls from.

    One field per SDD §3.6.1.2 design element in this increment's scope.

    Attributes:
        session: Session & Authentication Manager.
        workflow: Model Setup Data Workflow Manager.
    """

    session: SessionAndAuthenticationUseCase
    workflow: ModelSetupDataWorkflowUseCase


def build_panel_container(
    *,
    provisioning: Callable[[], ModelSetupDataProvisioning | None],
    queue: JobQueue,
    directory: DirectoryServicePort | None = None,
    database_url: str | None = None,
    jwt_secret: str | None = None,
    session_minutes: str | int | None = None,
    ldap_url: str | None = None,
    ldap_bind_dn_template: str | None = None,
    ldap_group_search_base: str | None = None,
    ldap_service_bind_dn: str | None = None,
    ldap_service_password: str | None = None,
    ldap_group_authorizations: str | None = None,
) -> PanelContainer:
    """Wire the panel from explicit collaborators and configuration.

    The two collaborators are passed rather than looked up here: which service
    satisfies them is the framework's decision, and taking them as arguments is
    what keeps this CSU independent of the CSU that provides them (SDD §2.3.1).

    Falls back to in-memory repositories when no database is configured, so the
    panel still runs without infrastructure — the only thing lost is what
    survives a restart.

    Args:
        provisioning: Resolves the currently registered Model Setup Data
            provisioning service, or None when none is. A callable rather than
            the service, because the framework replaces the reference when the
            provider restarts.
        queue: The host's deferral service, through which production runs.
        directory: Directory service to authenticate against; None builds the
            LDAP adapter from the settings below.
        database_url: Connection string for the panel's store; None keeps
            everything in memory.
        jwt_secret: Signing secret for issued session tokens.
        session_minutes: How long an issued token stays valid.
        ldap_url: LDAP URL.
        ldap_bind_dn_template: Template turning a username into a bind DN.
        ldap_group_search_base: Where to look for group entries.
        ldap_service_bind_dn: Read-only account the group search binds as.
        ldap_service_password: That account's password.
        ldap_group_authorizations: Which group grants which authorization.

    Returns:
        The wired container.

    Raises:
        RuntimeError: If no signing secret is configured, or the LDAP adapter is
            built without a directory to bind against.
    """
    clock = SystemClock()
    gateway = ServiceModelSetupDataGateway(provisioning)

    scopes: WorkingScopeRepository
    jobs: ProductionJobRepository
    statuses: SourceStatusRepository

    if database_url:
        engine = build_engine(database_url)
        create_schema(engine)
        scopes = PostgresWorkingScopeRepository(engine)
        jobs = PostgresProductionJobRepository(engine)
        statuses = PostgresSourceStatusRepository(engine)
    else:
        scopes = InMemoryWorkingScopeRepository()
        jobs = InMemoryProductionJobRepository()
        statuses = InMemorySourceStatusRepository()

    if directory is None:
        directory = LdapDirectoryService(
            server_url=ldap_url,
            bind_dn_template=ldap_bind_dn_template,
            group_search_base=ldap_group_search_base,
            service_bind_dn=ldap_service_bind_dn,
            service_password=ldap_service_password,
            group_authorizations=ldap_group_authorizations,
        )

    return PanelContainer(
        session=SessionAndAuthenticationUseCase(
            directory=directory,
            tokens=JwtTokenService(
                secret=jwt_secret, clock=clock, lifetime=_session_lifetime(session_minutes)
            ),
            gateway=gateway,
            scopes=scopes,
            clock=clock,
        ),
        workflow=ModelSetupDataWorkflowUseCase(
            gateway=gateway,
            jobs=jobs,
            queue=DeferringJobQueue(queue),
            scopes=scopes,
            statuses=statuses,
            clock=clock,
        ),
    )


def _session_lifetime(configured: str | int | None) -> timedelta:
    return timedelta(minutes=int(configured) if configured else DEFAULT_SESSION_MINUTES)
