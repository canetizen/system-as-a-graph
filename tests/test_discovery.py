"""
Description: Tests for how the platform decides which CSU bundles to install.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import pytest

from saag_platform.discovery import (
    BUNDLES_ENV_VAR,
    BUNDLES_EXCLUDE_ENV_VAR,
    CORE_BUNDLE,
    discover_bundles,
)


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a deployment's own composition settings out of these tests."""
    monkeypatch.delenv(BUNDLES_ENV_VAR, raising=False)
    monkeypatch.delenv(BUNDLES_EXCLUDE_ENV_VAR, raising=False)


def test_the_component_container_comes_first() -> None:
    """No CSU can be instantiated before the framework's own component
    container, so its position is a correctness requirement, not a convention."""
    assert discover_bundles()[0] == CORE_BUNDLE


def test_an_explicit_list_replaces_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deployments that deliberately run a subset, and tests that need a known
    composition, state the bundles outright rather than uninstalling CSUs."""
    monkeypatch.setenv(BUNDLES_ENV_VAR, " one.bundle , two.bundle ,, ")

    assert discover_bundles() == [CORE_BUNDLE, "one.bundle", "two.bundle"]


def test_an_explicit_list_ignores_the_exclusion_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Excluding from an explicit list would mean two ways to say the same thing
    and a question of which wins; the explicit list is simply the answer."""
    monkeypatch.setenv(BUNDLES_ENV_VAR, "one.bundle")
    monkeypatch.setenv(BUNDLES_EXCLUDE_ENV_VAR, "one")

    assert discover_bundles() == [CORE_BUNDLE, "one.bundle"]


def test_discovery_reports_modules_not_loaded_objects() -> None:
    """The framework performs the import, so a CSU that cannot be imported
    becomes a bundle that fails to start rather than an error that takes
    discovery — and with it the other nine CSUs — down."""
    assert all(isinstance(module, str) for module in discover_bundles())
