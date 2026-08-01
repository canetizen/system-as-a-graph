"""
Description: Configures the external data sources MSD acquires from (SRS MSD.2-5, 8).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from msd.src.model.data_source import (
    DataSourceConfiguration,
    DataSourceRegistry,
    DataSourceType,
)
from msd.src.ports.repositories import DataSourceConfigurationRepository


class ManageDataSourcesUseCase:
    """Records and retrieves per-source connection configuration.

    A source type holds many configurations, not one — several repositories,
    possibly several configuration databases — so every operation is keyed by
    ``(type, name)`` and listing returns the whole set.
    """

    def __init__(self, repository: DataSourceConfigurationRepository) -> None:
        """Initialize the use case.

        Args:
            repository: Store the configurations live in.
        """
        self._repository = repository

    def configure(self, configuration: DataSourceConfiguration) -> DataSourceConfiguration:
        """Save a source configuration, replacing one with the same key.

        Args:
            configuration: The configuration to save.

        Returns:
            The saved configuration.
        """
        self._repository.save(configuration)
        return configuration

    def remove(self, source_type: DataSourceType, name: str) -> bool:
        """Delete a source configuration.

        Args:
            source_type: Type of the source.
            name: Name of the source.

        Returns:
            True when a configuration was deleted.
        """
        return self._repository.delete(source_type, name)

    def get(self, source_type: DataSourceType, name: str) -> DataSourceConfiguration | None:
        """Fetch one configuration.

        Args:
            source_type: Type of the source.
            name: Name of the source.

        Returns:
            The configuration, or None when it is not configured.
        """
        return self._repository.get(source_type, name)

    def list_all(self) -> list[DataSourceConfiguration]:
        """Fetch every configured source."""
        return self._repository.list_all()

    def registry(self) -> DataSourceRegistry:
        """Build a registry over every configured source.

        Returns:
            A registry the acquisition use cases resolve adapters through.
        """
        return DataSourceRegistry(configurations=self._repository.list_all())

    def seed(self, configurations: list[DataSourceConfiguration]) -> list[DataSourceConfiguration]:
        """Save a starting set of configurations, skipping any already present.

        Lets a fresh deployment come up with a working multi-source setup while
        never overwriting what an operator has since edited.

        Args:
            configurations: Configurations to seed.

        Returns:
            The configurations actually saved.
        """
        saved: list[DataSourceConfiguration] = []
        for configuration in configurations:
            if self._repository.get(configuration.source_type, configuration.name) is None:
                self._repository.save(configuration)
                saved.append(configuration)
        return saved
