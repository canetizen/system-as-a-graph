"""
Description: Session & Authentication Manager design element (SRS VAE-01.3-4).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass

from saag_contracts.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef
from saag_vae_operations_panel.model.production_job import SelectableScope
from saag_vae_operations_panel.model.session import Authorization, Session
from saag_vae_operations_panel.model.working_scope import WorkingScope
from saag_vae_operations_panel.ports.directory_service import (
    AuthenticationFailed,
    DirectoryServicePort,
    TokenServicePort,
)
from saag_vae_operations_panel.ports.model_setup_data import ModelSetupDataGatewayPort
from saag_vae_operations_panel.ports.repositories import WorkingScopeRepository
from saag_vae_operations_panel.ports.support import ClockPort


class NotAuthorized(Exception):
    """Raised when an authenticated operator lacks the required authorization."""


@dataclass
class GrantedSession:
    """What a successful login returns.

    Attributes:
        token: The session token the caller presents on later requests.
        session: The session the token carries.
    """

    token: str
    session: Session


class SessionAndAuthenticationUseCase:
    """Authenticates operators, gates operations, and holds what they work on.

    VAE-01.3 asks for two things that are easy to conflate: only successfully
    authenticated users may access the system, *and* only within the scope of
    their authorizations. Authentication happens once at login; the second half
    is enforced on every request through ``authorize``.

    Selecting the working project/platform/system version belongs here too
    rather than to a separate element (SDD §3.6.1.2): the selection is part of
    a session — it is per operator, it is what every later operation is scoped
    to, and it is meaningless without one.
    """

    def __init__(
        self,
        directory: DirectoryServicePort,
        tokens: TokenServicePort,
        gateway: ModelSetupDataGatewayPort,
        scopes: WorkingScopeRepository,
        clock: ClockPort,
    ) -> None:
        """Initialize the use case.

        Args:
            directory: Directory service operators are authenticated against.
            tokens: Issues and verifies session tokens.
            gateway: Supplies the selectable projects, platforms, and versions.
            scopes: Store each operator's selection lives in.
            clock: Supplies the current time for expiry checks.
        """
        self._directory = directory
        self._tokens = tokens
        self._gateway = gateway
        self._scopes = scopes
        self._clock = clock

    def log_in(self, username: str, password: str) -> GrantedSession:
        """Authenticate an operator and start a session.

        Args:
            username: Directory account name.
            password: The account's password.

        Returns:
            The issued token and the session it carries.

        Raises:
            AuthenticationFailed: If the directory service refuses the
                credential.
        """
        user = self._directory.authenticate(username, password)
        token, session = self._tokens.issue(user)
        return GrantedSession(token=token, session=session)

    def authorize(self, token: str, required: Authorization) -> Session:
        """Verify a token and check it carries an authorization.

        Args:
            token: The session token presented by the caller.
            required: The authorization the operation needs.

        Returns:
            The verified session.

        Raises:
            AuthenticationFailed: If the token is invalid or expired.
            NotAuthorized: If the operator lacks the required authorization.
        """
        session = self._tokens.verify(token)
        if session.is_expired(self._clock.now()):
            raise AuthenticationFailed("Session has expired")

        if not session.user.may(required):
            raise NotAuthorized(
                f"'{session.user.username}' is not authorized to {required.value}"
            )

        return session

    def list_projects(self) -> SelectableScope:
        """List the selectable projects (SRS VAE-01.4)."""
        return SelectableScope(projects=self._gateway.list_projects())

    def list_platforms(self, project: str) -> SelectableScope:
        """List a project's selectable platforms (SRS VAE-01.4).

        Args:
            project: Project to list platforms for.
        """
        return SelectableScope(platforms=self._gateway.list_platforms(ProjectRef(project)))

    def list_versions(self, project: str, platform: str) -> SelectableScope:
        """List a platform's versions, with the effective one marked (SRS VAE-01.4).

        Args:
            project: Owning project.
            platform: Platform to list versions for.
        """
        return SelectableScope(
            versions=self._gateway.list_system_versions(
                PlatformRef(ProjectRef(project), platform)
            )
        )

    def select(self, username: str, scope: SystemVersionRef) -> WorkingScope:
        """Record what an operator has selected (SRS VAE-01.4).

        Selecting a different version clears any previously selected Model
        Setup Data file, since that file belongs to the version it was produced
        for and carrying it across would silently mismatch the two.

        Args:
            username: Operator making the selection.
            scope: The project/platform/system version chosen.

        Returns:
            The stored selection, with the effective-version mark filled in.
        """
        versions = self._gateway.list_system_versions(scope.platform)
        is_effective = any(
            version.version == scope.version and version.is_effective
            for version in versions
        )

        selection = WorkingScope(
            username=username, system_version=scope, selected_is_effective=is_effective
        )
        self._scopes.save(selection)
        return selection

    def current(self, username: str) -> WorkingScope | None:
        """Return an operator's current selection, or None when they have none.

        Args:
            username: Operator to look up.
        """
        return self._scopes.get(username)
