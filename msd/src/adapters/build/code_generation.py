"""
Description: Code generation adapters producing the generated sources extraction depends on.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from msd.src.model.version_inventory import SoftwareUnitVersion
from msd.src.ports.extraction import GenerationResult

#: Where generated sources are expected, relative to a unit's tree.
GENERATED_SUBDIRECTORY = "generated"


class GmakeCodeGenerator:
    """Runs the project's build target to regenerate a unit's sources.

    A non-zero exit is a failure. The prototype this replaces treated any
    completed run as success regardless of exit code, which let broken units
    reach extraction and silently contribute nothing.
    """

    def __init__(self, command: list[str], timeout_seconds: int) -> None:
        """Initialize the adapter.

        Args:
            command: Generation command, e.g. ``["gmake", "regenerate_code"]``.
            timeout_seconds: Kill the command after this long.
        """
        self._command = list(command)
        self._timeout_seconds = timeout_seconds

    def generate(self, unit: SoftwareUnitVersion, unit_tree: Path) -> GenerationResult:
        """Run the generation command in the unit's build directory.

        Args:
            unit: Software unit version being processed.
            unit_tree: Local root of that unit's transferred files.

        Returns:
            The outcome; failures are reported, never raised, so one broken
            unit does not abort the whole production run.
        """
        makefile = unit_tree / "Makefile"
        if not makefile.is_file():
            return GenerationResult(
                succeeded=False,
                reason=f"No Makefile in transferred tree for '{unit.versioned_name}'",
            )

        try:
            completed = subprocess.run(
                self._command,
                cwd=unit_tree,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return GenerationResult(
                succeeded=False,
                reason=f"Generation toolchain not available: {self._command[0]}",
            )
        except subprocess.TimeoutExpired:
            return GenerationResult(
                succeeded=False,
                reason=f"Generation timed out after {self._timeout_seconds}s",
            )

        if completed.returncode != 0:
            return GenerationResult(
                succeeded=False,
                reason=(
                    f"Generation failed for '{unit.versioned_name}' "
                    f"(exit code {completed.returncode})"
                ),
            )

        return GenerationResult(succeeded=True, generated_files=_generated_files(unit_tree))


class PrebuiltCodeGenerator:
    """Consumes generated sources that are already present in the unit tree.

    Used wherever the build toolchain is unavailable — CI, and any air-gapped
    environment shipping pre-generated output. The port contract is identical,
    so nothing downstream can tell the two apart.
    """

    def generate(self, unit: SoftwareUnitVersion, unit_tree: Path) -> GenerationResult:
        """Locate the unit's already-generated sources.

        Finding nothing is success, not failure: a unit that publishes no
        topics legitimately generates no TypeSupport sources. Whether a
        *required* generated file is missing is the mandatory-file policy's
        call, not this adapter's.

        Args:
            unit: Software unit version being processed.
            unit_tree: Local root of that unit's transferred files.

        Returns:
            Success with the files found, which may be an empty list.
        """
        del unit  # Located by tree, not by identity; kept for port conformance.
        return GenerationResult(succeeded=True, generated_files=_generated_files(unit_tree))


def _generated_files(unit_tree: Path) -> list[Path]:
    generated_root = unit_tree / GENERATED_SUBDIRECTORY
    if not generated_root.is_dir():
        return []
    return sorted(path for path in generated_root.rglob("*") if path.is_file())
