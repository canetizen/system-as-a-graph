"""
Description: Fixtures wiring the operations panel against stub adapters for tests.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import pytest

from saag_vae_operations_panel.testing.panel import Panel, build_panel

#: The account file the directory double reads, resolved from the installed
#: distribution rather than from a path relative to this repository.
PACKAGED_USERS_FILE = Path(
    str(resources.files("saag_vae_operations_panel.testing") / "users.json")
)


@pytest.fixture
def users_file(tmp_path: Path) -> Path:
    """A private copy of the account file, so a test may edit it."""
    target = tmp_path / "users.json"
    target.write_text(PACKAGED_USERS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return target


@pytest.fixture
def panel(users_file: Path) -> Panel:
    """A panel whose production runs inline."""
    return build_panel(users_file)
