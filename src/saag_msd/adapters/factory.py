"""
Description: Builds one outbound adapter instance per configured data source.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from saag_contracts.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from saag_msd.adapters.ansible.network_topology_source import (
    AnsibleNetworkTopologySource,
)
from saag_msd.adapters.git.source_code_repository import GitSourceCodeRepository
from saag_msd.adapters.rest.package_repository import RestPackageRepository
from saag_msd.adapters.sql.configuration_management_database import (
    SqlConfigurationManagementDatabase,
)
from saag_msd.model.data_source import (
    AccessMethod,
    DataSourceConfiguration,
    DataSourceRegistry,
    DataSourceType,
)
from saag_msd.model.source_files import FileClassifier
from saag_msd.ports.support import CredentialResolverPort


@dataclass
class AdapterContext:
    """Everything an adapter needs beyond its own configuration.

    Attributes:
        workspace: Directory transferred files are copied into.
        classifier: Assigns a kind to each transferred file.
        credentials: Resolves credential references at connection time.
    """

    workspace: Path
    classifier: FileClassifier
    credentials: CredentialResolverPort


class AdapterFactory:
    """Resolves ``(source type, access method)`` to a concrete adapter.

    This is the seam that makes several servers per interface ordinary: two
    Bitbucket instances are two adapter instances of one class, and a GitLab
    beside them is the same class again with a different address. Supporting a
    new protocol is a registration here plus a source configuration — no use
    case changes.
    """

    def __init__(self, context: AdapterContext) -> None:
        """Initialize the factory.

        Args:
            context: Shared construction inputs for every adapter.
        """
        self._context = context
        self._builders: dict[
            tuple[DataSourceType, AccessMethod],
            Callable[[DataSourceConfiguration, str | None], Any],
        ] = {
            (DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE, AccessMethod.SQL): (
                lambda configuration, secret: SqlConfigurationManagementDatabase(
                    configuration, password=secret
                )
            ),
            (DataSourceType.SOURCE_REPOSITORY, AccessMethod.GIT_HTTPS): (
                lambda configuration, secret: GitSourceCodeRepository(
                    configuration=configuration,
                    workspace=self._context.workspace,
                    classifier=self._context.classifier,
                    credential=secret,
                )
            ),
            (DataSourceType.PACKAGE_REPOSITORY, AccessMethod.REST): (
                lambda configuration, secret: RestPackageRepository(
                    configuration, credential=secret
                )
            ),
            (DataSourceType.NETWORK_TOPOLOGY, AccessMethod.ANSIBLE): (
                lambda configuration, secret: AnsibleNetworkTopologySource(configuration)
            ),
        }

    def register(
        self,
        source_type: DataSourceType,
        access_method: AccessMethod,
        builder: Callable[[DataSourceConfiguration, str | None], Any],
    ) -> None:
        """Register an adapter for a source type and access method.

        Tests use this to install doubles without standing up the real
        technologies; a new vendor uses it to join the roster.

        Args:
            source_type: Type the adapter serves.
            access_method: Protocol the adapter speaks.
            builder: Receives the configuration and the resolved credential.
        """
        self._builders[(source_type, access_method)] = builder

    def supports(self, configuration: DataSourceConfiguration) -> bool:
        """Whether an adapter is registered for a configuration."""
        return (configuration.source_type, configuration.access_method) in self._builders

    def build(self, configuration: DataSourceConfiguration) -> Any:
        """Build the adapter for one configured source.

        Credentials are resolved here rather than stored, so a source whose
        secret is unset fails with an authorization error instead of silently
        connecting anonymously.

        Args:
            configuration: The source to build an adapter for.

        Returns:
            The adapter instance.

        Raises:
            AcquisitionFailure: If no adapter is registered for this source
                type and access method, or the configured credential cannot be
                resolved.
        """
        builder = self._builders.get(
            (configuration.source_type, configuration.access_method)
        )
        if builder is None:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{configuration.name}' is configured with access method "
                f"'{configuration.access_method.value}', which no adapter serves",
                detail=f"source_type={configuration.source_type.value}",
            )

        secret = None
        if configuration.credential is not None:
            secret = self._context.credentials.resolve(configuration.credential)

        return builder(configuration, secret)

    def build_all(
        self, registry: DataSourceRegistry, source_type: DataSourceType
    ) -> list[Any]:
        """Build an adapter for every configured source of one type.

        Args:
            registry: The configured sources.
            source_type: Type to build adapters for.

        Returns:
            Adapters in priority order. Manually-entered sources are absent:
            their data *is* their configuration, so there is nothing to connect
            to and the use case reads them directly.

        Raises:
            AcquisitionFailure: If any other configured source cannot be built.
                A source that quietly vanished from the run would look exactly
                like a source nobody configured, which is the one thing an
                operator must never have to guess about.
        """
        return [
            self.build(configuration)
            for configuration in registry.of_type(source_type)
            if configuration.access_method is not AccessMethod.MANUAL
        ]
