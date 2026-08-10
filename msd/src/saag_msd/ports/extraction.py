"""
Description: Outbound ports for code generation and structural extraction over ingested files.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from saag_msd.model.extraction import ExtractionResult
from saag_msd.model.source_files import SourceFileRecord
from saag_msd.model.version_inventory import SoftwareUnitVersion


@dataclass
class GenerationResult:
    """Outcome of generating code for one software unit.

    Attributes:
        succeeded: Whether generation produced usable output.
        reason: Failure cause; empty on success.
        generated_files: Files produced (or found already present), relative to
            the unit tree.
    """

    succeeded: bool
    reason: str = ""
    generated_files: list[Path] = field(default_factory=list)


@runtime_checkable
class CodeGenerationPort(Protocol):
    """Produces the generated sources structural extraction depends on.

    The TypeSupport definitions carrying topic size and QoS are not files that
    exist in the repository — they are generated inside each unit's tree by the
    project's build. Extraction therefore cannot run before this port has, and
    a deployment without the toolchain uses an adapter that consumes
    already-generated output instead.
    """

    def generate(self, unit: SoftwareUnitVersion, unit_tree: Path) -> GenerationResult:
        """Generate (or locate) a unit's generated sources.

        Never raises for a build failure: a failing unit must not abort the
        whole run, so the outcome is reported and the caller excludes just
        that unit.

        Args:
            unit: Software unit version being processed.
            unit_tree: Local root of that unit's transferred files.

        Returns:
            The generation outcome.
        """
        ...


@runtime_checkable
class StructuralExtractorPort(Protocol):
    """Extracts entities and relations from ingested files.

    Every extractor reads only files MSD itself transferred or generated, so
    the fake and real profiles differ solely in where those files came from.
    """

    @property
    def name(self) -> str:
        """Extractor name, recorded as the origin of what it produces."""
        ...

    def extract(
        self, unit: SoftwareUnitVersion, files: list[SourceFileRecord]
    ) -> ExtractionResult:
        """Extract from one unit's transferred files.

        Args:
            unit: Software unit version the files belong to.
            files: That unit's transferred files.

        Returns:
            Entities and relations found; empty when this extractor has nothing
            to say about the unit.

        Raises:
            AcquisitionFailure: If a file it is responsible for is unparsable.
        """
        ...


@runtime_checkable
class ModelWideExtractorPort(Protocol):
    """Extracts from files describing the model as a whole, not one unit.

    The system deployment descriptor is the case this exists for: it lives in
    one repository, describes every unit's placement, and must be read once per
    model rather than once per unit.
    """

    @property
    def name(self) -> str:
        """Extractor name, recorded as the origin of what it produces."""
        ...

    def extract(self, files: list[SourceFileRecord]) -> ExtractionResult:
        """Extract from every file transferred for the model.

        Args:
            files: All transferred files, across all repositories.

        Returns:
            Entities and relations found.

        Raises:
            AcquisitionFailure: If the file it is responsible for is missing or
                unparsable.
        """
        ...
