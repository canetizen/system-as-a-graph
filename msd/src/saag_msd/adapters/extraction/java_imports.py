"""
Description: Extracts inter-unit dependencies from Java import statements.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from saag_contracts.documents.model_setup_data import NodeType, RelationType
from saag_msd.model.extraction import ExtractedRelation, ExtractionResult
from saag_msd.model.source_files import SourceFileKind, SourceFileRecord
from saag_msd.model.version_inventory import SoftwareUnitVersion

_IMPORT_PATTERN = re.compile(r"^\s*import\s+(?:static\s+)?([^;]+);", re.MULTILINE)
_COMMENT_PATTERN = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)
_PACKAGE_SEGMENT_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class JavaImportExtractor:
    """Derives ``depends_on`` relations from imports under a configured domain prefix.

    An import of ``<prefix>.<name>....`` where ``<name>`` carries one of the
    configured suffixes means this unit depends on that unit. Declarative
    evidence, which is what the descriptor-level model is built from.
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        """Initialize the extractor.

        Args:
            settings: ``import_domain_prefix`` and ``dependency_suffixes`` from
                the rules file.
        """
        self._domain_prefix = str(settings.get("import_domain_prefix", "")).strip()
        self._suffixes = tuple(settings.get("dependency_suffixes", []))

    @property
    def name(self) -> str:
        """Extractor name, recorded as the origin of what it produces."""
        return "java_imports"

    def extract(
        self, unit: SoftwareUnitVersion, files: list[SourceFileRecord]
    ) -> ExtractionResult:
        """Extract dependency relations for one unit.

        Args:
            unit: Software unit version the files belong to.
            files: That unit's transferred files.

        Returns:
            One ``depends_on`` relation per distinct dependency found; a unit
            never depends on itself.
        """
        result = ExtractionResult()
        if not self._domain_prefix:
            return result

        dependencies: set[str] = set()
        for record in files:
            if record.kind is not SourceFileKind.SOURCE_CODE:
                continue
            dependencies.update(self._dependencies_in(record))

        for dependency in sorted(dependencies - {unit.unit_name}):
            result.relations.append(
                ExtractedRelation(
                    relation_type=RelationType.DEPENDS_ON,
                    source_type=NodeType.CSU,
                    source_name=unit.unit_name,
                    target_type=NodeType.CSU,
                    target_name=dependency,
                    origin=self.name,
                )
            )

        return result

    def _dependencies_in(self, record: SourceFileRecord) -> set[str]:
        try:
            raw = Path(record.local_path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # A source file that cannot be read yields no dependency evidence;
            # its absence is caught by the mandatory-file check, not here.
            return set()

        content = _COMMENT_PATTERN.sub("", raw)
        found: set[str] = set()
        prefix = f"{self._domain_prefix}."
        for target in _IMPORT_PATTERN.findall(content):
            normalized = target.strip()
            if not normalized.startswith(prefix):
                continue

            segment = normalized[len(prefix) :].split(".", 1)[0].strip()
            if not _PACKAGE_SEGMENT_PATTERN.match(segment):
                continue
            if self._suffixes and not segment.endswith(self._suffixes):
                continue

            found.add(segment)

        return found
