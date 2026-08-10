"""
Description: TC-MSD-04 — Source Repository Ingestion (SRS MSD.17-20).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import pytest
from saag_contracts.errors.acquisition import AcquisitionStatus

from saag_msd.model.data_source import DataSourceType
from saag_msd.use_cases._recording import RunRecorder


@pytest.fixture
def recorder(harness):
    """A recorder scoped to the test's platform."""
    return RunRecorder(
        run_id="tc04", platform=harness.scope.platform, errors=harness.errors, clock=harness.clock
    )


def test_files_transfer_with_their_metadata_recorded(harness, recorder):
    """Name, path, package/version, and update time are recorded per file (SRS MSD.18)."""
    inventory = harness.record_inventory()

    result = harness.ingestion().ingest(inventory.entries, recorder)

    descriptor = next(
        record for record in result.files if record.file_path == "src/nav_app.xml"
    )
    assert descriptor.file_name == "nav_app.xml"
    assert descriptor.package == "nav_app"
    assert descriptor.version == "1.2.0"
    assert descriptor.updated_at is not None


def test_units_route_across_several_repositories(harness, recorder):
    """Each unit is taken from the repository that holds it, and files say which."""
    inventory = harness.record_inventory()

    result = harness.ingestion().ingest(inventory.entries, recorder)

    attribution = {record.package: record.source_name for record in result.files}
    assert attribution["nav_app"] == "bitbucket-a"
    assert attribution["sensor_app"] == "bitbucket-b"
    assert attribution["helper_lib"] == "gitlab-main"
    assert sorted(result.sources_used) == ["bitbucket-a", "bitbucket-b", "gitlab-main"]


def test_a_missing_mandatory_file_yields_missing_data(harness, recorder):
    """A unit missing a mandatory file is excluded and recorded (SRS MSD.19)."""
    (harness.unit_path("bitbucket-a", "nav_app_1.2.0") / "install" / "install.sh").unlink()
    inventory = harness.record_inventory()

    result = harness.ingestion().ingest(inventory.entries, recorder)

    assert "nav_app" in result.excluded_units
    assert "install" in result.excluded_units["nav_app"]

    error = next(
        item
        for item in harness.errors.list_for_run("tc04")
        if item.source_name == "bitbucket-a"
    )
    assert error.status is AcquisitionStatus.MISSING_DATA
    assert error.source_type == DataSourceType.SOURCE_REPOSITORY.value


@pytest.mark.parametrize(
    "injected",
    [
        AcquisitionStatus.ACCESS_ERROR,
        AcquisitionStatus.AUTHORIZATION_ERROR,
        AcquisitionStatus.INTEGRITY_ERROR,
    ],
)
def test_each_transfer_fault_is_recorded_and_costs_only_its_own_repository(
    harness, recorder, injected
):
    """One repository failing must not take the others down with it (SRS MSD.20)."""
    harness.faults.faults["bitbucket-b"] = {"transfer": injected}
    inventory = harness.record_inventory()

    result = harness.ingestion().ingest(inventory.entries, recorder)

    assert "sensor_app" in result.excluded_units
    assert {record.package for record in result.files} == {
        "system_repo",
        "nav_app",
        "helper_lib",
    }

    error = next(
        item
        for item in harness.errors.list_for_run("tc04")
        if item.source_name == "bitbucket-b"
    )
    assert error.status is injected


def test_a_unit_no_repository_holds_names_every_source_tried(harness, recorder):
    """An unroutable unit is a missing-data record naming the repositories consulted."""
    from saag_msd.model.version_inventory import SoftwareUnitVersion

    units = [SoftwareUnitVersion(unit_name="ghost_app", version="9.9.9")]

    result = harness.ingestion().ingest(units, recorder)

    assert "ghost_app" in result.excluded_units
    reason = result.excluded_units["ghost_app"]
    assert "bitbucket-a" in reason
    assert "bitbucket-b" in reason
    assert "gitlab-main" in reason
