"""
Description: Guards the workspace layout against directory names that break imports.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _members() -> list[str]:
    configuration = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    return configuration["tool"]["uv"]["workspace"]["members"]


@pytest.mark.parametrize("member", _members())
def test_no_member_directory_shadows_a_standard_library_module(member: str) -> None:
    """A member directory whose name matches a standard-library module shadows it
    for anything that puts the repository root on the import path.

    This is not hypothetical. The framework host lived in `platform/`, and running
    the whole test suite made that directory the `platform` module, so the LDAP
    library's `from platform import system` failed and the panel could not be
    imported at all — with an error naming neither this repository nor the cause.
    The directory is now `platform_host/`, and this test is what keeps the next
    member from reintroducing the trap.
    """
    name = Path(member).name

    assert name not in sys.stdlib_module_names, (
        f"member directory {member!r} shadows the standard-library module {name!r}"
    )


@pytest.mark.parametrize("member", _members())
def test_every_member_is_a_distribution_with_its_own_tests(member: str) -> None:
    """Each member must be independently buildable and independently testable —
    the property that lets it move to its own repository unchanged."""
    directory = REPOSITORY_ROOT / member

    assert (directory / "pyproject.toml").is_file(), member
    assert (directory / "src").is_dir(), member
    assert list((directory / "tests").glob("test_*.py")), member
