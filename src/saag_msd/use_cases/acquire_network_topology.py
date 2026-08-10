"""
Description: Acquires network topology automatically or from manual entry (SRS MSD.5-7).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from saag_contracts.errors.acquisition import AcquisitionFailure
from saag_contracts.types.identifiers import PlatformRef

from saag_msd.model.data_source import (
    AccessMethod,
    DataSourceConfiguration,
    DataSourceType,
)
from saag_msd.model.network_topology import (
    NetworkComponent,
    NetworkTopology,
    TopologyAcquisitionMethod,
)
from saag_msd.ports.external_sources import NetworkTopologySourcePort
from saag_msd.ports.repositories import DataSourceConfigurationRepository
from saag_msd.use_cases._recording import RunRecorder

#: Source name a manually entered topology is recorded under, so it is
#: attributable in exactly the way a fetched one is.
MANUAL_SOURCE_NAME = "manual-entry"


class AcquireNetworkTopologyUseCase:
    """Obtains network topology by either supported method.

    Automatic acquisition reads the configured sources; manual entry bypasses
    them entirely, since it originates with the operator. Both produce the same
    domain object, so nothing downstream has to know which was used — only the
    recorded method distinguishes them.

    A manually entered topology is saved as the *configuration* of a manual
    topology source rather than in a store of its own: MSD.8 already makes
    per-source configuration savable, and for a manual source the parameters
    the operator typed are what that source consists of.
    """

    def __init__(
        self,
        sources: list[NetworkTopologySourcePort],
        configurations: DataSourceConfigurationRepository,
    ) -> None:
        """Initialize the use case.

        Args:
            sources: One adapter per configured topology source, in priority
                order.
            configurations: Store manually entered topology is saved in.
        """
        self._sources = sources
        self._configurations = configurations

    def resolve(self, platform: PlatformRef, recorder: RunRecorder) -> NetworkTopology | None:
        """Return the topology a production run should use.

        A topology the operator entered for this platform wins over an
        automatic fetch: it is the more deliberate statement of the two, and
        entering one only to have it ignored would make MSD.7 pointless.

        Args:
            platform: Platform to resolve topology for.
            recorder: Failure recorder for this run.

        Returns:
            The topology to use, or None when neither method supplied one.
        """
        entered = self.stored_manual(platform)
        if entered is not None:
            return entered
        return self.acquire(platform, recorder)

    def acquire(self, platform: PlatformRef, recorder: RunRecorder) -> NetworkTopology | None:
        """Fetch the topology automatically from the configured sources (SRS MSD.6).

        Args:
            platform: Platform to fetch topology for.
            recorder: Failure recorder for this run.

        Returns:
            The first non-empty topology found, or None when no source supplied
            one — which callers record as not supplied rather than filling in.
        """
        for source in self._sources:
            try:
                topology = source.fetch(platform)
            except AcquisitionFailure as failure:
                recorder.record_failure(
                    failure,
                    source_name=source.source_name,
                    source_type=DataSourceType.NETWORK_TOPOLOGY.value,
                )
                continue

            if not topology.is_empty:
                return topology

        return None

    def enter_manually(
        self, platform: PlatformRef, components: list[NetworkComponent]
    ) -> NetworkTopology:
        """Record a topology the operator entered by hand (SRS MSD.7).

        The entry is saved per platform, so entering one platform's topology
        never overwrites another's.

        Args:
            platform: Platform the entry applies to.
            components: Components the operator described.

        Returns:
            The entered topology, marked as manually acquired.
        """
        existing = self._configurations.get(
            DataSourceType.NETWORK_TOPOLOGY, MANUAL_SOURCE_NAME
        )
        parameters = dict(existing.parameters) if existing else {}
        parameters[self._platform_key(platform)] = [
            {
                "name": component.name,
                "component_type": component.component_type,
                "attributes": dict(component.attributes),
            }
            for component in components
        ]

        self._configurations.save(
            DataSourceConfiguration(
                source_type=DataSourceType.NETWORK_TOPOLOGY,
                name=MANUAL_SOURCE_NAME,
                access_method=AccessMethod.MANUAL,
                connection_address="",
                credential=None,
                priority=existing.priority if existing else 0,
                parameters=parameters,
            )
        )

        return NetworkTopology(
            method=TopologyAcquisitionMethod.MANUAL,
            source_name=MANUAL_SOURCE_NAME,
            components=list(components),
        )

    def stored_manual(self, platform: PlatformRef) -> NetworkTopology | None:
        """Return the topology the operator entered for a platform, if any.

        Args:
            platform: Platform to look up.

        Returns:
            The entered topology, or None when nothing was entered for it.
        """
        configuration = self._configurations.get(
            DataSourceType.NETWORK_TOPOLOGY, MANUAL_SOURCE_NAME
        )
        if configuration is None:
            return None

        entries = configuration.parameters.get(self._platform_key(platform))
        if not entries:
            return None

        return NetworkTopology(
            method=TopologyAcquisitionMethod.MANUAL,
            source_name=MANUAL_SOURCE_NAME,
            components=[
                NetworkComponent(
                    name=entry["name"],
                    component_type=entry.get("component_type", ""),
                    attributes=dict(entry.get("attributes", {})),
                )
                for entry in entries
            ],
        )

    @staticmethod
    def _platform_key(platform: PlatformRef) -> str:
        return f"{platform.project.name}/{platform.name}"
