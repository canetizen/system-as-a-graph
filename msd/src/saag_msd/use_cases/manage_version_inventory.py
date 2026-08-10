"""
Description: Records and updates the Software Unit Version Inventory (SRS MSD.14-15).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from saag_contracts.types.identifiers import SystemVersionRef

from saag_msd.model.version_inventory import (
    SoftwareUnitVersion,
    SoftwareUnitVersionInventory,
)
from saag_msd.ports.repositories import VersionInventoryRepository


class ManageVersionInventoryUseCase:
    """Keeps the per-system-version record of which software units run where."""

    def __init__(self, repository: VersionInventoryRepository) -> None:
        """Initialize the use case.

        Args:
            repository: Store the inventory lives in.
        """
        self._repository = repository

    def record(
        self, system_version: SystemVersionRef, units: list[SoftwareUnitVersion]
    ) -> SoftwareUnitVersionInventory:
        """Record the baseline inventory for a system version (SRS MSD.14).

        Existing candidate entries are preserved: re-reading the baseline from
        the configuration management database must not discard a candidate an
        evaluation is already running against.

        Args:
            system_version: Scope to record for.
            units: Baseline software unit versions.

        Returns:
            The stored inventory.
        """
        inventory = self._repository.get(system_version) or SoftwareUnitVersionInventory(
            system_version=system_version
        )
        candidates = inventory.candidates

        inventory = SoftwareUnitVersionInventory(system_version=system_version)
        for unit in units:
            inventory.record(unit)
        for candidate in candidates:
            inventory.add_candidate(candidate)

        self._repository.save(inventory)
        return inventory

    def add_candidate(
        self, system_version: SystemVersionRef, candidate: SoftwareUnitVersion
    ) -> SoftwareUnitVersionInventory:
        """Add a candidate version alongside the defined versions (SRS MSD.15).

        Args:
            system_version: Scope to update.
            candidate: Candidate software unit version under evaluation.

        Returns:
            The updated inventory.
        """
        inventory = self._repository.get(system_version) or SoftwareUnitVersionInventory(
            system_version=system_version
        )
        inventory.add_candidate(candidate)
        self._repository.save(inventory)
        return inventory

    def get(self, system_version: SystemVersionRef) -> SoftwareUnitVersionInventory | None:
        """Fetch the recorded inventory.

        Args:
            system_version: Scope to fetch.

        Returns:
            The inventory, or None when nothing has been recorded yet.
        """
        return self._repository.get(system_version)
