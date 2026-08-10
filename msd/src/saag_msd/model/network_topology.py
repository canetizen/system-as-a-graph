"""
Description: Network topology data and its two acquisition methods (SRS MSD.5-7).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TopologyAcquisitionMethod(str, Enum):
    """How network topology data was obtained (SRS MSD.6-7)."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"


@dataclass(frozen=True)
class NetworkComponent:
    """One network component of the target system.

    Attributes:
        name: Component name.
        component_type: Component kind as reported by the source (switch,
            router, segment, ...); carried through verbatim, not normalized.
        attributes: Further attributes reported by the source.
    """

    name: str
    component_type: str
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Machine:
    """One operator console or processor unit the topology source reports.

    The deployment descriptor names the units software runs on; the topology
    source knows the same machines from the other side — their addresses,
    groups, and hardware. Both are the same node in the end, merged by name.

    Attributes:
        name: Machine name, matched against the deployment descriptor's.
        attributes: Whatever the source reported about it.
    """

    name: str
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NetworkTopology:
    """Network topology acquired for one project/platform/system version.

    Attributes:
        method: Whether it was obtained automatically or entered manually.
        source_name: Configured source it came from; for manual entry, the
            name under which the operator's entry was recorded.
        components: The network components reported.
        machines: The machines reported, if the source knows about them.
            Manual entry supplies none — an operator types a topology, not an
            inventory.
    """

    method: TopologyAcquisitionMethod
    source_name: str
    components: list[NetworkComponent] = field(default_factory=list)
    machines: list[Machine] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """Whether the topology carries nothing at all."""
        return not self.components and not self.machines
