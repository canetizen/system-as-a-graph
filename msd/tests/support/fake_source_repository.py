"""
Description: In-test source repository double serving the stand-in unit trees from disk.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from msd.src.model.data_source import DataSourceConfiguration
from msd.src.model.source_files import FileClassifier, SourceFileRecord
from msd.src.model.version_inventory import SoftwareUnitVersion
from msd.tests.support.doubles import FaultPolicy
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus

#: Unit trees the stand-in Gitea server is seeded from. Tests read them
#: straight off disk so ingestion and extraction see the same content the real
#: git adapter would clone.
REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[3] / "tests" / "standins" / "data" / "source_repository"
)


class FakeSourceCodeRepository:
    """Serves one repository's unit trees from the stand-in seed directory.

    Transfer copies the tree into the run workspace rather than reading it in
    place, so code generation and extraction downstream run against transferred
    files exactly as they do behind the real git adapter.
    """

    def __init__(
        self,
        configuration: DataSourceConfiguration,
        workspace: Path,
        classifier: FileClassifier,
        faults: FaultPolicy | None = None,
        root: Path | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            configuration: The repository this instance serves.
            workspace: Directory transferred files are copied into.
            classifier: Assigns a kind to each transferred file.
            faults: Fault injection policy.
            root: Seed tree root; defaults to the stand-in tree.
        """
        self._configuration = configuration
        self._workspace = workspace
        self._classifier = classifier
        self._faults = faults or FaultPolicy()
        self._root = (Path(root) if root else REPOSITORY_ROOT) / configuration.name

    @property
    def source_name(self) -> str:
        """Name of the configured repository this instance serves."""
        return self._configuration.name

    def holds(self, unit: SoftwareUnitVersion) -> bool:
        """Whether this repository holds a unit version (never raises on a miss)."""
        return (self._root / unit.versioned_name).is_dir()

    def check_access(self) -> None:
        """Verify the repository answers, honouring any injected fault.

        Raises:
            AcquisitionFailure: Whatever fault is injected for this source, or
                ACCESS_ERROR when the repository is not present at all.
        """
        self._faults.check(self.source_name, "transfer")

        if not self._root.is_dir():
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"Repository '{self.source_name}' is not reachable at "
                f"{self._configuration.connection_address}",
            )

    def local_tree(self, unit: SoftwareUnitVersion) -> Path:
        """Return the workspace root this unit is transferred into.

        Args:
            unit: Software unit version to locate.

        Returns:
            Local root path; populated only after a successful transfer.
        """
        return self._workspace / self.source_name / unit.versioned_name

    def transfer(self, unit: SoftwareUnitVersion) -> list[SourceFileRecord]:
        """Copy a unit's files into the workspace and record their metadata.

        Args:
            unit: Software unit version to transfer.

        Returns:
            One record per transferred file (SRS MSD.18).

        Raises:
            AcquisitionFailure: ACCESS_ERROR when this repository does not hold
                the unit, or whatever fault is injected for this source.
        """
        self._faults.check(self.source_name, "transfer")

        unit_root = self._root / unit.versioned_name
        if not unit_root.is_dir():
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{unit.versioned_name}' not found in repository '{self.source_name}'",
            )

        destination = self.local_tree(unit)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(unit_root, destination)

        records: list[SourceFileRecord] = []
        for copied in sorted(destination.rglob("*")):
            if not copied.is_file():
                continue

            relative = copied.relative_to(destination).as_posix()
            records.append(
                SourceFileRecord(
                    file_name=copied.name,
                    file_path=relative,
                    package=unit.unit_name,
                    version=unit.version,
                    updated_at=datetime.fromtimestamp(copied.stat().st_mtime, tz=UTC),
                    source_name=self.source_name,
                    kind=self._classifier.classify(relative),
                    local_path=str(copied),
                )
            )

        return records
