"""
Description: Software Unit Version Inventory and its candidate-version rule (SRS MSD.14-15).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from saag_contracts.types.identifiers import SystemVersionRef

#: Version parts are padded to this length so "1.2" and "1.2.0" compare equal.
_VERSION_PART_COUNT = 3

_LEADING_DIGITS = re.compile(r"(\d+)")


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of integers.

    Tolerates the shapes real tags come in — ``v1.0.0``, ``1.0.0``,
    ``2.1.3-beta``, ``1_0_0`` — because tag conventions differ per repository
    and the inventory must order them anyway.

    Args:
        version: Version or tag string.

    Returns:
        Integer tuple of at least three parts, zero-padded. A string with no
        digits at all yields ``(0, 0, 0)``, which sorts lowest.
    """
    normalized = version.lstrip("vV").split("-")[0]

    parts: list[int] = []
    for part in re.split(r"[._]", normalized):
        match = _LEADING_DIGITS.match(part)
        if match:
            parts.append(int(match.group(1)))

    while len(parts) < _VERSION_PART_COUNT:
        parts.append(0)

    return tuple(parts)


@dataclass(frozen=True)
class SoftwareUnitVersion:
    """One software unit at one version, as it will run in the system.

    Attributes:
        unit_name: Software unit name.
        version: Version/tag of the unit.
        source_name: Configured source repository that holds it, when the
            configuration management database assigns one explicitly. Empty
            means "resolve by searching the configured repositories".
        is_candidate: Whether this entry is a candidate version submitted for
            installation evaluation (SRS MSD.15) rather than a baseline entry.
    """

    unit_name: str
    version: str
    source_name: str = ""
    is_candidate: bool = False

    @property
    def versioned_name(self) -> str:
        """Name used for repository folders and file naming, e.g. ``abc_1.0.0``."""
        return f"{self.unit_name}_{self.version}"

    @property
    def sort_key(self) -> tuple[int, ...]:
        """Comparable version key."""
        return parse_version(self.version)


@dataclass
class SoftwareUnitVersionInventory:
    """The recorded inventory for one project/platform/system version.

    Attributes:
        system_version: Scope this inventory belongs to.
        entries: Inventory entries, baseline and candidate alike.
    """

    system_version: SystemVersionRef
    entries: list[SoftwareUnitVersion] = field(default_factory=list)

    def record(self, entry: SoftwareUnitVersion) -> None:
        """Record a baseline entry, replacing any existing entry for that unit.

        Args:
            entry: The baseline entry to record.
        """
        self.entries = [
            existing for existing in self.entries if existing.unit_name != entry.unit_name
        ]
        self.entries.append(replace(entry, is_candidate=False))

    def add_candidate(self, entry: SoftwareUnitVersion) -> None:
        """Add a candidate version alongside the already-defined versions.

        SRS MSD.15 requires the candidate to sit *together with* the other
        defined versions, so the baseline entry for the same unit is kept. Only
        a previous candidate for that unit is displaced, since one evaluation
        run carries one candidate per unit.

        Args:
            entry: The candidate entry to add.
        """
        self.entries = [
            existing
            for existing in self.entries
            if not (existing.unit_name == entry.unit_name and existing.is_candidate)
        ]
        self.entries.append(replace(entry, is_candidate=True))

    @property
    def baseline(self) -> list[SoftwareUnitVersion]:
        """Baseline entries only, in unit-name order."""
        return sorted(
            (entry for entry in self.entries if not entry.is_candidate),
            key=lambda entry: entry.unit_name,
        )

    @property
    def candidates(self) -> list[SoftwareUnitVersion]:
        """Candidate entries only, in unit-name order."""
        return sorted(
            (entry for entry in self.entries if entry.is_candidate),
            key=lambda entry: entry.unit_name,
        )

    def latest_of(self, unit_name: str) -> SoftwareUnitVersion | None:
        """Return the highest-versioned entry for a unit.

        Args:
            unit_name: Unit to look up.

        Returns:
            The highest-versioned entry, or None when the unit is not recorded.
        """
        matching = [entry for entry in self.entries if entry.unit_name == unit_name]
        if not matching:
            return None
        return max(matching, key=lambda entry: entry.sort_key)
