"""
Description: TC-MSD-03 — Software Unit Version Inventory Manager (SRS MSD.14-15).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from msd.src.model.version_inventory import SoftwareUnitVersion, parse_version


def test_baseline_inventory_is_recorded_for_the_scope(harness):
    """The units defined for a system version are recorded (SRS MSD.14)."""
    inventory = harness.record_inventory()

    assert {entry.unit_name: entry.version for entry in inventory.baseline} == {
        "system_repo": "1.0.0",
        "nav_app": "1.2.0",
        "sensor_app": "2.0.1",
        "helper_lib": "1.0.0",
    }
    assert inventory.candidates == []


def test_candidate_is_added_without_displacing_the_defined_versions(harness):
    """A candidate sits alongside the baseline entries (SRS MSD.15)."""
    harness.record_inventory()

    updated = harness.inventory.add_candidate(
        harness.scope, SoftwareUnitVersion(unit_name="nav_app", version="1.3.0")
    )

    assert [entry.version for entry in updated.candidates] == ["1.3.0"]
    baseline = {entry.unit_name: entry.version for entry in updated.baseline}
    assert baseline["nav_app"] == "1.2.0"
    assert len(baseline) == 4


def test_rereading_the_baseline_preserves_an_existing_candidate(harness):
    """Refreshing from the CM database must not discard a running evaluation."""
    harness.record_inventory()
    harness.inventory.add_candidate(
        harness.scope, SoftwareUnitVersion(unit_name="nav_app", version="1.3.0")
    )

    refreshed = harness.record_inventory()

    assert [entry.version for entry in refreshed.candidates] == ["1.3.0"]


def test_latest_version_lookup_orders_by_semantic_version(harness):
    """The inventory orders versions numerically, not lexically."""
    harness.record_inventory()
    harness.inventory.add_candidate(
        harness.scope, SoftwareUnitVersion(unit_name="nav_app", version="1.10.0")
    )

    inventory = harness.inventory.get(harness.scope)

    assert inventory.latest_of("nav_app").version == "1.10.0"
    assert parse_version("v1.10.0") > parse_version("1.9.9")
    assert parse_version("2.1.3-beta") == (2, 1, 3)
