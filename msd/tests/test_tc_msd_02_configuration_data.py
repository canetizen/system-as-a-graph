"""
Description: TC-MSD-02 — Configuration Data Acquisition (SRS MSD.9-13, 16).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import pytest

from saag_contracts.errors.acquisition import AcquisitionStatus
from saag_contracts.types.identifiers import ProjectRef
from saag_msd.model.data_source import DataSourceType
from saag_msd.use_cases._recording import RunRecorder


@pytest.fixture
def recorder(harness):
    """A recorder scoped to the test's platform."""
    return RunRecorder(
        run_id="tc02", platform=harness.scope.platform, errors=harness.errors, clock=harness.clock
    )


def test_project_platform_and_version_are_retrieved(harness, recorder):
    """Project, platform, and version information comes from the CM database."""
    projects = harness.configuration_data().list_projects(recorder)
    assert [item.ref.name for item in projects.data.projects] == ["skyline"]

    platforms = harness.configuration_data().list_platforms(ProjectRef("skyline"), recorder)
    assert [item.ref.name for item in platforms.data.platforms] == ["avionics"]

    versions = harness.configuration_data().list_system_versions(
        harness.scope.platform, recorder
    )
    assert [item.ref.version for item in versions.data.versions] == ["1.0.0", "0.9.0"]


def test_the_effective_version_is_marked(harness, recorder):
    """Exactly one returned version carries the effective mark (SRS MSD.13)."""
    outcome = harness.configuration_data().list_system_versions(harness.scope.platform, recorder)

    effective = outcome.data.effective_version
    assert effective is not None
    assert effective.ref.version == "1.0.0"
    assert [item.is_effective for item in outcome.data.versions].count(True) == 1


@pytest.mark.parametrize(
    ("injected", "expected"),
    [
        (AcquisitionStatus.MISSING_DATA, AcquisitionStatus.MISSING_DATA),
        (AcquisitionStatus.ACCESS_ERROR, AcquisitionStatus.ACCESS_ERROR),
        (AcquisitionStatus.FORMAT_INCOMPATIBLE, AcquisitionStatus.FORMAT_INCOMPATIBLE),
    ],
)
def test_each_fault_marks_the_acquisition_with_an_error_status(
    harness, recorder, injected, expected
):
    """Deficiency, access error, and format incompatibility each error the run (SRS MSD.16)."""
    harness.faults.faults["cmdb-primary"] = {"list_projects": injected}

    outcome = harness.configuration_data().list_projects(recorder)

    assert outcome.status is expected
    assert outcome.data.projects == []
    assert len(outcome.errors) == 1


def test_a_recorded_failure_carries_its_full_attribution(harness, recorder):
    """Every failure names its source, scope, and time (SRS MSD.22)."""
    harness.faults.faults["cmdb-primary"] = {"list_projects": AcquisitionStatus.ACCESS_ERROR}

    harness.configuration_data().list_projects(recorder)

    error = harness.errors.list_for_run("tc02")[0]
    assert error.source_name == "cmdb-primary"
    assert error.source_type == DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE.value
    assert error.platform.project.name == "skyline"
    assert error.platform.name == "avionics"
    assert error.occurred_at == harness.clock.now()
    assert error.reason


def test_a_failed_source_does_not_look_like_an_empty_inventory(harness):
    """Recording the inventory surfaces the acquisition status (SRS MSD.16)."""
    harness.faults.faults["cmdb-primary"] = {
        "list_software_units": AcquisitionStatus.ACCESS_ERROR
    }
    recorder = RunRecorder(
        run_id="tc02", platform=harness.scope.platform, errors=harness.errors, clock=harness.clock
    )

    units, outcome = harness.configuration_data().list_software_units(
        harness.scope.platform, "1.0.0", recorder
    )

    assert units == []
    assert outcome.status is AcquisitionStatus.ACCESS_ERROR
    assert outcome.errors
