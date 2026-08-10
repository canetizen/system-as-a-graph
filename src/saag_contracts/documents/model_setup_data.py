"""
Description: Model Setup Data file schema exchanged from MSD to CSM-01 over INT-IF-01.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

#: Bumped whenever the on-disk layout changes incompatibly. CSM-01 refuses a
#: document whose major version it does not implement (SRS CSM-01.3).
SCHEMA_VERSION = "1.0"


class NodeType(str, Enum):
    """Node types the Core System Model represents (SRS CSM-01.6-17)."""

    SYSTEM = "system"
    SOFTWARE_SEGMENT = "software_segment"
    CSCI = "csci"
    CSC = "csc"
    CSU = "csu"
    ROLE = "role"
    TOPIC = "topic"
    MESSAGE = "message"
    PROCESSOR_UNIT = "processor_unit"
    NETWORK_COMPONENT = "network_component"
    MIDDLEWARE_SERVICE = "middleware_service"
    COMMUNICATION_SERVICE = "communication_service"


class RelationType(str, Enum):
    """Relationship types the Core System Model represents (SRS CSM-01.18-23)."""

    RUNS_ON = "runs_on"
    USES_SERVICE = "uses_service"
    PUBLISHES = "publishes"
    CONSUMES = "consumes"
    DEPENDS_ON = "depends_on"
    ASSIGNED_TO_ROLE = "assigned_to_role"


@dataclass(frozen=True)
class EntityRecord:
    """One node destined for the Core System Model.

    Attributes:
        node_type: Which of the 12 node types this is.
        name: Entity name, unique per node type within one document.
        attributes: Queryable attributes carried through verbatim from the
            source (CPU allocation, OS settings, QoS, size, ...). Values are
            never defaulted or invented; an attribute absent at the source is
            absent here.
    """

    node_type: NodeType
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the document's JSON shape."""
        return {
            "node_type": self.node_type.value,
            "name": self.name,
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityRecord:
        """Rebuild from the document's JSON shape.

        Raises:
            ValueError: If node_type is not a known node type.
        """
        return cls(
            node_type=NodeType(data["node_type"]),
            name=data["name"],
            attributes=dict(data.get("attributes", {})),
        )


@dataclass(frozen=True)
class RelationRecord:
    """One relationship destined for the Core System Model.

    Endpoints are given as (node type, name) pairs rather than opaque ids so the
    document stays readable and CSM-01 can detect a dangling endpoint as an
    invalid-relationship error (SRS CSM-01.25).

    Attributes:
        relation_type: Which of the 6 relationship types this is.
        source_type: Node type of the source endpoint.
        source_name: Name of the source endpoint.
        target_type: Node type of the target endpoint.
        target_name: Name of the target endpoint.
        attributes: Relationship attributes carried through from the source.
    """

    relation_type: RelationType
    source_type: NodeType
    source_name: str
    target_type: NodeType
    target_name: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the document's JSON shape."""
        return {
            "relation_type": self.relation_type.value,
            "source": {"node_type": self.source_type.value, "name": self.source_name},
            "target": {"node_type": self.target_type.value, "name": self.target_name},
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelationRecord:
        """Rebuild from the document's JSON shape.

        Raises:
            ValueError: If a type field is not a known node/relationship type.
        """
        return cls(
            relation_type=RelationType(data["relation_type"]),
            source_type=NodeType(data["source"]["node_type"]),
            source_name=data["source"]["name"],
            target_type=NodeType(data["target"]["node_type"]),
            target_name=data["target"]["name"],
            attributes=dict(data.get("attributes", {})),
        )


@dataclass(frozen=True)
class SourceFileEntry:
    """Provenance record for one file the model was derived from (SRS MSD.18).

    Attributes:
        file_name: File name as obtained from the repository.
        file_path: Path of the file within its repository.
        package: Package/software unit the file belongs to.
        version: Package version the file was obtained at.
        updated_at: The file's update timestamp at the source.
        source_name: Configured data source the file came from — required
            because one model draws files from several repositories.
    """

    file_name: str
    file_path: str
    package: str
    version: str
    updated_at: datetime
    source_name: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the document's JSON shape."""
        return {
            "file_name": self.file_name,
            "file_path": self.file_path,
            "package": self.package,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
            "source_name": self.source_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceFileEntry:
        """Rebuild from the document's JSON shape."""
        return cls(
            file_name=data["file_name"],
            file_path=data["file_path"],
            package=data["package"],
            version=data["version"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            source_name=data["source_name"],
        )


@dataclass(frozen=True)
class Provenance:
    """How and from what a document was produced.

    Attributes:
        produced_at: When MSD assembled the document.
        run_id: Identifier of the MSD production run.
        sources: Names of every configured data source consulted.
        excluded_units: Software units left out of the model, mapped to why.
            Populated when a unit's acquisition, generation, or validation
            failed; the remaining units still produce a usable document.
        not_supplied: Node types no configured source provided data for.
            Recorded explicitly so a genuine gap is never mistaken for an
            empty result — and never filled with invented values.
    """

    produced_at: datetime
    run_id: str
    sources: list[str] = field(default_factory=list)
    excluded_units: dict[str, str] = field(default_factory=dict)
    not_supplied: list[NodeType] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the document's JSON shape."""
        return {
            "produced_at": self.produced_at.isoformat(),
            "run_id": self.run_id,
            "sources": list(self.sources),
            "excluded_units": dict(self.excluded_units),
            "not_supplied": [node_type.value for node_type in self.not_supplied],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Provenance:
        """Rebuild from the document's JSON shape."""
        return cls(
            produced_at=datetime.fromisoformat(data["produced_at"]),
            run_id=data["run_id"],
            sources=list(data.get("sources", [])),
            excluded_units=dict(data.get("excluded_units", {})),
            not_supplied=[NodeType(value) for value in data.get("not_supplied", [])],
        )


@dataclass(frozen=True)
class ModelSetupDataDocument:
    """The Model Setup Data file itself (SRS MSD.23, INT-IF-01).

    Only data that passed MSD's verification checks appears here; everything
    that failed is absent and accounted for in ``provenance``.

    Attributes:
        project: Project the model is scoped to.
        platform: Platform the model is scoped to.
        system_version: System version the model is scoped to.
        entities: Nodes for the Core System Model.
        relations: Relationships for the Core System Model.
        source_files: Provenance for every file the model was derived from.
        provenance: How the document was produced and what it omits.
        schema_version: Layout version of this document.
    """

    project: str
    platform: str
    system_version: str
    entities: list[EntityRecord]
    relations: list[RelationRecord]
    source_files: list[SourceFileEntry]
    provenance: Provenance
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Serialize the whole document to its JSON shape."""
        return {
            "schema_version": self.schema_version,
            "project": self.project,
            "platform": self.platform,
            "system_version": self.system_version,
            "entities": [entity.to_dict() for entity in self.entities],
            "relations": [relation.to_dict() for relation in self.relations],
            "source_files": [source_file.to_dict() for source_file in self.source_files],
            "provenance": self.provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelSetupDataDocument:
        """Rebuild a document from its JSON shape.

        Raises:
            KeyError: If a mandatory top-level field is missing.
            ValueError: If an enum-valued field carries an unknown value.
        """
        return cls(
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            project=data["project"],
            platform=data["platform"],
            system_version=data["system_version"],
            entities=[EntityRecord.from_dict(item) for item in data["entities"]],
            relations=[RelationRecord.from_dict(item) for item in data["relations"]],
            source_files=[SourceFileEntry.from_dict(item) for item in data["source_files"]],
            provenance=Provenance.from_dict(data["provenance"]),
        )
