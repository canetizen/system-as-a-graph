"""
Description: Tests how the framework host offers deployment settings to components.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import pytest

from saag_platform.bootstrap import (
    PROFILE_PROPERTY,
    environment_property,
    framework_properties,
)


def test_an_environment_variable_becomes_a_declarable_property(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A CSU declares the property name, so the rule turning a variable into one
    is part of the contract between host and CSU, not an implementation detail."""
    monkeypatch.setenv("MSD_WORKSPACE_DIR", "/var/lib/saag/workspace")

    properties = framework_properties("api")

    assert environment_property("MSD_WORKSPACE_DIR") == "saag.env.msd_workspace_dir"
    assert properties["saag.env.msd_workspace_dir"] == "/var/lib/saag/workspace"


def test_the_host_names_no_setting_of_its_own(monkeypatch: pytest.MonkeyPatch) -> None:
    """The mapping is mechanical on purpose: a table of known settings would have
    to name each CSU's variables, so adding a CSU would mean editing the host."""
    monkeypatch.setenv("A_SETTING_NO_CSU_HAS_YET", "value")

    properties = framework_properties("api")

    assert properties["saag.env.a_setting_no_csu_has_yet"] == "value"


def test_the_profile_is_reported_separately(monkeypatch: pytest.MonkeyPatch) -> None:
    """Which process the framework serves is the host's own statement, so an
    environment variable must not be able to contradict it."""
    monkeypatch.setenv("SAAG_PROFILE", "not-this")

    assert framework_properties("worker")[PROFILE_PROPERTY] == "worker"
