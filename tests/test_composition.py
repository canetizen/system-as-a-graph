"""
Description: Tests that the deployed composition is the one this repository declares.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import tomllib
from importlib.metadata import Distribution, PackageNotFoundError, entry_points, version
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

#: Distributions of the CSCI that are not CSUs: the shared contracts every CSU
#: depends on, and the framework host that installs them. Neither publishes a
#: bundle, because neither is a component.
NOT_A_CSU = {"saag-contracts", "saag-platform"}


def _declared() -> list[str]:
    """The distributions this repository says make up a deployment."""
    configuration = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    return [
        requirement.split(">")[0].split("<")[0].split("=")[0].strip()
        for requirement in configuration["project"]["dependencies"]
        if requirement.startswith("saag-")
    ]


def test_the_declaration_covers_the_whole_csci() -> None:
    """Guards the list below against silently shrinking, which would make every
    other assertion here weaker rather than failing."""
    declared = _declared()

    assert len(declared) == 12, declared
    assert NOT_A_CSU <= set(declared)


@pytest.mark.parametrize("distribution", _declared())
def test_every_declared_distribution_is_installed(distribution: str) -> None:
    """A composition that resolves is not the same as one that installed: this is
    what turns a version this repository names into something actually present."""
    try:
        assert version(distribution)
    except PackageNotFoundError:  # pragma: no cover - the assertion is the report
        pytest.fail(f"{distribution} is declared but not installed")


@pytest.mark.parametrize("distribution", sorted(set(_declared()) - NOT_A_CSU))
def test_every_declared_csu_publishes_a_bundle(distribution: str) -> None:
    """A CSU is added to the CSCI by being installed, which only works if it
    declares the entry point the framework host discovers it through (SDD §2.5).
    A CSU that shipped without one would install silently and never run."""
    owners = {
        point.name: Distribution.from_name(distribution).metadata["Name"]
        for point in entry_points(group="saag.bundles")
        if point.dist and point.dist.metadata["Name"] == distribution
    }

    assert owners, f"{distribution} publishes no saag.bundles entry point"


def test_nothing_runs_that_this_repository_did_not_declare() -> None:
    """The direction that matters for a deployment: the framework installs what it
    discovers, so anything discoverable and undeclared is in the CSCI by accident."""
    declared = set(_declared())
    discovered = {
        point.dist.metadata["Name"]
        for point in entry_points(group="saag.bundles")
        if point.dist
    }

    assert discovered <= declared, sorted(discovered - declared)
