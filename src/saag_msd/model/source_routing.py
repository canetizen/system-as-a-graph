"""
Description: Resolves which configured repository holds a given software unit (SRS MSD.17, 19).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from saag_msd.model.data_source import DataSourceConfiguration, DataSourceType
from saag_msd.model.version_inventory import SoftwareUnitVersion


@dataclass(frozen=True)
class SourceRoute:
    """The repository a software unit's files are to be taken from.

    Attributes:
        unit: The software unit version being routed.
        configuration: Repository chosen for it.
        assigned: True when the configuration management database named this
            repository explicitly; False when it was found by searching.
    """

    unit: SoftwareUnitVersion
    configuration: DataSourceConfiguration
    assigned: bool


@dataclass(frozen=True)
class UnroutableUnit:
    """A software unit no configured repository could supply.

    Attributes:
        unit: The software unit version that could not be routed.
        sources_tried: Names of every repository consulted, so the resulting
            missing-data record names them rather than saying "not found".
    """

    unit: SoftwareUnitVersion
    sources_tried: list[str]


class SourceRouter:
    """Chooses a source repository per software unit.

    Resolution order (SRS MSD.17): an explicit per-unit assignment carried in
    the Software Unit Version Inventory wins; otherwise the configured
    repositories are searched in priority order and the first that holds the
    unit wins. A unit found nowhere becomes an ``UnroutableUnit``, which the
    caller turns into a missing-data record (SRS MSD.19).
    """

    def __init__(self, configurations: list[DataSourceConfiguration]) -> None:
        """Initialize the router.

        Args:
            configurations: Configured sources; non-repository types are
                ignored, so callers may pass the whole registry.
        """
        self._repositories = sorted(
            (
                configuration
                for configuration in configurations
                if configuration.source_type == DataSourceType.SOURCE_REPOSITORY
            ),
            key=lambda configuration: (configuration.priority, configuration.name),
        )

    @property
    def repositories(self) -> list[DataSourceConfiguration]:
        """Configured source repositories, in search order."""
        return list(self._repositories)

    def route(
        self,
        units: list[SoftwareUnitVersion],
        holds_unit: Callable[[DataSourceConfiguration, SoftwareUnitVersion], bool],
    ) -> tuple[list[SourceRoute], list[UnroutableUnit]]:
        """Route every unit to a repository.

        Args:
            units: Software unit versions to route.
            holds_unit: Predicate answering whether a repository holds a unit;
                supplied by the caller because only an adapter can answer it.

        Returns:
            A ``(routes, unroutable)`` pair. Both lists preserve input order.
        """
        routes: list[SourceRoute] = []
        unroutable: list[UnroutableUnit] = []

        for unit in units:
            if unit.source_name:
                assigned = self._by_name(unit.source_name)
                if assigned is not None:
                    routes.append(SourceRoute(unit=unit, configuration=assigned, assigned=True))
                    continue

            tried: list[str] = []
            found = False
            for configuration in self._repositories:
                tried.append(configuration.name)
                if holds_unit(configuration, unit):
                    routes.append(
                        SourceRoute(unit=unit, configuration=configuration, assigned=False)
                    )
                    found = True
                    break

            if not found:
                unroutable.append(UnroutableUnit(unit=unit, sources_tried=tried))

        return routes, unroutable

    def _by_name(self, name: str) -> DataSourceConfiguration | None:
        for configuration in self._repositories:
            if configuration.name == name:
                return configuration
        return None
