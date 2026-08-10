"""
Description: Extracts topic size and QoS from the generated TypeSupport sources.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from saag_contracts.documents.model_setup_data import NodeType
from saag_contracts.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from saag_msd.model.extraction import ExtractedEntity, ExtractionResult
from saag_msd.model.source_files import SourceFileKind, SourceFileRecord
from saag_msd.model.version_inventory import SoftwareUnitVersion


class TypeSupportExtractor:
    """Reads topic attributes out of the sources the build generates.

    The generated format is described entirely by the rules file — the topic
    name pattern and one pattern per attribute — so a change to what the build
    emits is a configuration edit. Attributes the patterns do not find are left
    absent rather than defaulted, which is what makes the downstream
    mandatory-field check meaningful.
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        """Initialize the extractor.

        Args:
            settings: ``topic_name_pattern`` and the ``field_patterns`` map.

        Raises:
            re.error: If a configured pattern is not a valid regular expression.
        """
        self._topic_name_pattern = re.compile(
            settings.get("topic_name_pattern", r"TOPIC_NAME\s*=\s*\"([^\"]+)\"")
        )
        self._field_patterns = {
            field: re.compile(pattern)
            for field, pattern in settings.get("field_patterns", {}).items()
        }

    @property
    def name(self) -> str:
        """Extractor name, recorded as the origin of what it produces."""
        return "type_support"

    def extract(
        self, unit: SoftwareUnitVersion, files: list[SourceFileRecord]
    ) -> ExtractionResult:
        """Extract topic attributes from one unit's generated sources.

        Args:
            unit: Software unit version the files belong to.
            files: That unit's transferred and generated files.

        Returns:
            One topic entity per generated TypeSupport source, carrying
            whatever attributes the configured patterns matched.

        Raises:
            AcquisitionFailure: FORMAT_INCOMPATIBLE when a generated source
                carries no recognizable topic name, since that means the
                configured format no longer matches what the build emits.
        """
        del unit  # Topic identity comes from the generated source, not the unit.
        result = ExtractionResult()

        for record in files:
            if record.kind is not SourceFileKind.GENERATED_TYPE_SUPPORT:
                continue

            content = Path(record.local_path).read_text(encoding="utf-8")
            match = self._topic_name_pattern.search(content)
            if match is None:
                raise AcquisitionFailure(
                    AcquisitionStatus.FORMAT_INCOMPATIBLE,
                    f"No topic name found in generated source '{record.file_path}'",
                    detail="type_support_extraction patterns do not match this file",
                )

            attributes: dict[str, Any] = {}
            for field, pattern in self._field_patterns.items():
                field_match = pattern.search(content)
                if field_match is not None:
                    attributes[field] = field_match.group(1)

            result.entities.append(
                ExtractedEntity(
                    node_type=NodeType.TOPIC,
                    name=match.group(1),
                    attributes=attributes,
                    origin=self.name,
                )
            )

        return result
