"""
Description: Extracts unit placement, roles, and criticality from the system deployment descriptor.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

from msd.src.model.extraction import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from msd.src.model.source_files import SourceFileKind, SourceFileRecord
from shared.contracts.model_setup_data import NodeType, RelationType
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus


class SystemDescriptorExtractor:
    """Reads the deployment descriptor that ships inside one of the repositories.

    This is where a unit's processor/console placement, its roles, and its
    criticality come from. It is a model-wide file rather than a per-unit one:
    it describes every unit at once, is transferred like any other file, and is
    parsed on the same code path as everything else — there is no separate data
    source behind it.
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        """Initialize the extractor.

        Args:
            settings: Element and attribute names from the rules file.
        """
        self._unit_element = settings.get("unit_element", "unit")
        self._unit_name_attribute = settings.get("unit_name_attribute", "name")
        self._processor_unit_attribute = settings.get("processor_unit_attribute", "runs_on")
        self._role_element = settings.get("role_element", "role")
        self._role_name_attribute = settings.get("role_name_attribute", "name")
        self._criticality_attribute = settings.get("criticality_attribute", "criticality")

    @property
    def name(self) -> str:
        """Extractor name, recorded as the origin of what it produces."""
        return "system_descriptor"

    def extract(self, files: list[SourceFileRecord]) -> ExtractionResult:
        """Extract placement, roles, and criticality for the whole model.

        Args:
            files: All transferred files, across all repositories.

        Returns:
            Processor unit and role nodes, the CSU entries carrying criticality,
            and the ``runs_on`` / ``assigned_to_role`` relations.

        Raises:
            AcquisitionFailure: MISSING_DATA when no descriptor was transferred,
                FORMAT_INCOMPATIBLE when it is not well-formed XML.
        """
        descriptors = [
            record
            for record in files
            if record.kind is SourceFileKind.SYSTEM_DEPLOYMENT_DESCRIPTOR
        ]
        if not descriptors:
            raise AcquisitionFailure(
                AcquisitionStatus.MISSING_DATA,
                "No system deployment descriptor was obtained from any repository",
            )

        result = ExtractionResult()
        for record in descriptors:
            result.merge(self._read(record))
        return result

    def _read(self, record: SourceFileRecord) -> ExtractionResult:
        try:
            root = ElementTree.parse(record.local_path).getroot()
        except ElementTree.ParseError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.FORMAT_INCOMPATIBLE,
                f"System deployment descriptor '{record.file_path}' is not well-formed XML",
                detail=str(exc),
            ) from exc

        result = ExtractionResult()
        for element in root.iter(self._unit_element):
            unit_name = element.get(self._unit_name_attribute)
            if not unit_name:
                continue

            criticality = element.get(self._criticality_attribute)
            result.entities.append(
                ExtractedEntity(
                    node_type=NodeType.CSU,
                    name=unit_name,
                    attributes={"criticality": criticality} if criticality else {},
                    origin=self.name,
                )
            )

            processor_unit = element.get(self._processor_unit_attribute)
            if processor_unit:
                result.entities.append(
                    ExtractedEntity(
                        node_type=NodeType.PROCESSOR_UNIT,
                        name=processor_unit,
                        origin=self.name,
                    )
                )
                result.relations.append(
                    ExtractedRelation(
                        relation_type=RelationType.RUNS_ON,
                        source_type=NodeType.CSU,
                        source_name=unit_name,
                        target_type=NodeType.PROCESSOR_UNIT,
                        target_name=processor_unit,
                        origin=self.name,
                    )
                )

            for role_element in element.iter(self._role_element):
                role_name = role_element.get(self._role_name_attribute)
                if not role_name:
                    continue

                result.entities.append(
                    ExtractedEntity(
                        node_type=NodeType.ROLE, name=role_name, origin=self.name
                    )
                )
                result.relations.append(
                    ExtractedRelation(
                        relation_type=RelationType.ASSIGNED_TO_ROLE,
                        source_type=NodeType.CSU,
                        source_name=unit_name,
                        target_type=NodeType.ROLE,
                        target_name=role_name,
                        origin=self.name,
                    )
                )

        return result
