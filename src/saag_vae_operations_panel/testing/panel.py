"""
Description: A wired operations panel over stubs, for this CSU's tests and its consumers'.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from saag_contracts.types.identifiers import (
    PlatformRef,
    ProjectRef,
    SystemVersionRef,
    system_version,
)

from saag_vae_operations_panel.adapters.jwt_tokens import JwtTokenService
from saag_vae_operations_panel.adapters.memory import (
    InMemoryProductionJobRepository,
    InMemorySourceStatusRepository,
    InMemoryWorkingScopeRepository,
)
from saag_vae_operations_panel.model.production_job import (
    AvailableSystemVersion,
    ModelSetupDataFile,
    ProductionError,
)
from saag_vae_operations_panel.model.source_status import Accessibility, SourceStatus
from saag_vae_operations_panel.ports.model_setup_data import ProductionOutcome
from saag_vae_operations_panel.testing import InlineProductionQueue
from saag_vae_operations_panel.testing.fake_directory_service import (
    FakeDirectoryService,
)
from saag_vae_operations_panel.use_cases.manage_model_setup_data import (
    ModelSetupDataWorkflowUseCase,
)
from saag_vae_operations_panel.use_cases.manage_session import (
    SessionAndAuthenticationUseCase,
)

#: The scope every test works in.
PROJECT = "skyline"
PLATFORM = "avionics"
EFFECTIVE_VERSION = "1.0.0"
OLDER_VERSION = "0.9.0"

FIXED_NOW = datetime(2026, 7, 31, 9, 30, tzinfo=UTC)


class FixedClock:
    """Returns a pinned time, so token expiry and job timing are deterministic."""

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        """Return the pinned time."""
        return self._moment


@dataclass
class StubModelSetupDataGateway:
    """Stands in for MSD so the panel's tests exercise only the panel.

    Attributes:
        files: Files reported as produced for the scope.
        errors: Failures reported for the platform.
        sources: Accessibility results the probe returns.
        outcome: What the next production run returns.
        raises: When set, production raises this instead of returning.
        produced: Scopes production was invoked for, in order.
    """

    files: list[ModelSetupDataFile] = field(default_factory=list)
    errors: list[ProductionError] = field(default_factory=list)
    sources: list[SourceStatus] = field(default_factory=list)
    outcome: ProductionOutcome | None = None
    raises: Exception | None = None
    produced: list[SystemVersionRef] = field(default_factory=list)

    def list_projects(self) -> list[str]:
        """List the one project the stub knows."""
        return [PROJECT]

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List the one platform the stub knows."""
        return [PLATFORM] if project.name == PROJECT else []

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List two versions, the newer one marked effective."""
        if platform.name != PLATFORM:
            return []
        return [
            AvailableSystemVersion(version=EFFECTIVE_VERSION, is_effective=True),
            AvailableSystemVersion(version=OLDER_VERSION, is_effective=False),
        ]

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFile]:
        """List the configured files."""
        del system_version
        return list(self.files)

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Return the configured outcome, or raise the configured failure."""
        self.produced.append(system_version)
        if self.raises is not None:
            raise self.raises
        return self.outcome or ProductionOutcome(run_id=run_id, succeeded=True)

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceStatus]:
        """Return the configured accessibility results."""
        del platform
        return list(self.sources)

    def list_errors(self, platform: PlatformRef) -> list[ProductionError]:
        """Return the configured failures."""
        del platform
        return list(self.errors)


@dataclass
class Panel:
    """A wired operations panel with its stub gateway exposed.

    Attributes:
        gateway: The stub MSD gateway the test configures, or None when the
            caller supplied a gateway of its own.
        session: Session & Authentication Manager.
        workflow: Model Setup Data Workflow Manager.
        clock: The pinned clock.
    """

    gateway: StubModelSetupDataGateway | None
    session: SessionAndAuthenticationUseCase
    workflow: ModelSetupDataWorkflowUseCase
    clock: FixedClock

    def log_in(self, username: str = "operator", password: str = "operator"):
        """Log in and return the granted session."""
        return self.session.log_in(username, password)

    def select_effective_scope(self, username: str = "operator"):
        """Select the effective version, the common starting point for tests."""
        return self.session.select(
            username, system_version(PROJECT, PLATFORM, EFFECTIVE_VERSION)
        )


def build_panel(users_file: Path, queue=None, gateway=None) -> Panel:
    """Wire the panel against stubs and in-memory stores.

    Args:
        users_file: Account file the directory service reads.
        queue: Job queue to use; the default runs production inline.
        gateway: Model Setup Data gateway to use; the default is the stub below.
            Supplied when a test needs a real gateway — for instance one whose
            provisioning service is absent.

    Returns:
        The wired panel. ``Panel.gateway`` is the stub for the test to configure,
        and is None when a gateway was supplied instead.
    """
    clock = FixedClock(FIXED_NOW)
    stub = None
    if gateway is None:
        stub = StubModelSetupDataGateway(
            sources=[
                SourceStatus(
                    source_type="configuration_management_database",
                    source_name="cmdb-primary",
                    accessibility=Accessibility.REACHABLE,
                    checked_at=FIXED_NOW,
                )
            ]
        )
        gateway = stub

    scopes = InMemoryWorkingScopeRepository()

    workflow = ModelSetupDataWorkflowUseCase(
        gateway=gateway,
        jobs=InMemoryProductionJobRepository(),
        queue=queue or InlineProductionQueue(lambda: workflow),
        scopes=scopes,
        statuses=InMemorySourceStatusRepository(),
        clock=clock,
    )

    return Panel(
        gateway=stub,
        session=SessionAndAuthenticationUseCase(
            directory=FakeDirectoryService(users_file),
            tokens=JwtTokenService(
                clock=clock,
                lifetime=timedelta(hours=8),
                secret="test-secret-long-enough-for-hmac-sha256",
            ),
            gateway=gateway,
            scopes=scopes,
            clock=clock,
        ),
        workflow=workflow,
        clock=clock,
    )
