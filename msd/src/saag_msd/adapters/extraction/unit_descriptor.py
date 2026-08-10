"""
Description: Extracts publish/consume relations from each unit's XML descriptor.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

from saag_contracts.documents.model_setup_data import NodeType, RelationType
from saag_contracts.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from saag_msd.model.extraction import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from saag_msd.model.source_files import SourceFileKind, SourceFileRecord
from saag_msd.model.version_inventory import SoftwareUnitVersion

#: A role of this value means the unit both publishes and consumes the topic,
#: and expands into one relation of each kind.
_PUBSUB_ROLE = "pubsub"

_ROLE_RELATIONS = {
    "pub": (RelationType.PUBLISHES,),
    "sub": (RelationType.CONSUMES,),
    _PUBSUB_ROLE: (RelationType.PUBLISHES, RelationType.CONSUMES),
}


class UnitDescriptorExtractor:
    """Reads topic declarations from a unit's ``<unit>.xml`` descriptor.

    Produces the topic nodes and the publish/consume relations, but no QoS: the
    descriptor declares *what* a unit talks about, while the generated
    TypeSupport sources describe *how*. The two are merged downstream.
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        """Initialize the extractor.

        Args:
            settings: Element and attribute names plus the dummy-topic list,
                taken from the rules file so a differently-shaped descriptor is
                a configuration change.
        """
        self._topic_element = settings.get("topic_element", "topic")
        self._name_attribute = settings.get("name_attribute", "name")
        self._role_attribute = settings.get("role_attribute", "role")
        self._dummy_topics = {
            name.strip().lower() for name in settings.get("dummy_topic_names", [])
        }

    @property
    def name(self) -> str:
        """Extractor name, recorded as the origin of what it produces."""
        return "unit_descriptor"

    def extract(
        self, unit: SoftwareUnitVersion, files: list[SourceFileRecord]
    ) -> ExtractionResult:
        """Extract topic nodes and pub/sub relations for one unit.

        Args:
            unit: Software unit version the files belong to.
            files: That unit's transferred files.

        Returns:
            Topics and their publish/consume relations; empty when the unit has
            no descriptor or declares no topics.

        Raises:
            AcquisitionFailure: FORMAT_INCOMPATIBLE when a descriptor is not
                well-formed XML.
        """
        result = ExtractionResult()

        for record in files:
            if record.kind is not SourceFileKind.UNIT_DESCRIPTOR:
                continue

            for topic_name, roles in self._read_topics(record):
                result.entities.append(
                    ExtractedEntity(
                        node_type=NodeType.TOPIC,
                        name=topic_name,
                        origin=self.name,
                    )
                )
                for relation_type in roles:
                    result.relations.append(
                        ExtractedRelation(
                            relation_type=relation_type,
                            source_type=NodeType.CSU,
                            source_name=unit.unit_name,
                            target_type=NodeType.TOPIC,
                            target_name=topic_name,
                            origin=self.name,
                        )
                    )

        return result

    def _read_topics(
        self, record: SourceFileRecord
    ) -> list[tuple[str, tuple[RelationType, ...]]]:
        try:
            root = ElementTree.parse(record.local_path).getroot()
        except ElementTree.ParseError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.FORMAT_INCOMPATIBLE,
                f"Unit descriptor '{record.file_path}' is not well-formed XML",
                detail=str(exc),
            ) from exc

        topics: list[tuple[str, tuple[RelationType, ...]]] = []
        for element in root.iter(self._topic_element):
            topic_name = element.get(self._name_attribute)
            role = (element.get(self._role_attribute) or "").strip().lower()

            if not topic_name or role not in _ROLE_RELATIONS:
                continue
            if topic_name.strip().lower() in self._dummy_topics:
                continue

            topics.append((topic_name, _ROLE_RELATIONS[role]))

        return topics
