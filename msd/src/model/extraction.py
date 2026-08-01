"""
Description: Entities and relations extracted from ingested source files, in CSM-01 vocabulary.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from shared.contracts.model_setup_data import (
    EntityRecord,
    NodeType,
    RelationRecord,
    RelationType,
)


@dataclass(frozen=True)
class ExtractedEntity:
    """A node discovered while extracting from ingested files.

    Deliberately mirrors the contract's ``EntityRecord`` rather than inventing
    a parallel vocabulary: extraction speaks CSM-01's node types from the start,
    so assembly is a filter, not a translation.

    Attributes:
        node_type: Node type this entity becomes.
        name: Entity name.
        attributes: Attributes read from the source; never defaulted.
        origin: Extractor that produced it, for provenance and debugging.
    """

    node_type: NodeType
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    origin: str = ""

    @property
    def key(self) -> tuple[NodeType, str]:
        """Identity used to deduplicate entities across extractors."""
        return (self.node_type, self.name)

    def to_contract(self) -> EntityRecord:
        """Convert to the Model Setup Data file's entity record."""
        return EntityRecord(
            node_type=self.node_type,
            name=self.name,
            attributes=dict(self.attributes),
        )


@dataclass(frozen=True)
class ExtractedRelation:
    """A relationship discovered while extracting from ingested files.

    Attributes:
        relation_type: Relationship type this becomes.
        source_type: Node type of the source endpoint.
        source_name: Name of the source endpoint.
        target_type: Node type of the target endpoint.
        target_name: Name of the target endpoint.
        attributes: Attributes read from the source.
        origin: Extractor that produced it.
    """

    relation_type: RelationType
    source_type: NodeType
    source_name: str
    target_type: NodeType
    target_name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    origin: str = ""

    @property
    def key(self) -> tuple[RelationType, NodeType, str, NodeType, str]:
        """Identity used to deduplicate relations across extractors."""
        return (
            self.relation_type,
            self.source_type,
            self.source_name,
            self.target_type,
            self.target_name,
        )

    def to_contract(self) -> RelationRecord:
        """Convert to the Model Setup Data file's relation record."""
        return RelationRecord(
            relation_type=self.relation_type,
            source_type=self.source_type,
            source_name=self.source_name,
            target_type=self.target_type,
            target_name=self.target_name,
            attributes=dict(self.attributes),
        )


@dataclass
class ExtractionResult:
    """What one extractor produced from the files it was given.

    Attributes:
        entities: Entities discovered.
        relations: Relations discovered.
    """

    entities: list[ExtractedEntity] = field(default_factory=list)
    relations: list[ExtractedRelation] = field(default_factory=list)

    def merge(self, other: ExtractionResult) -> None:
        """Absorb another result, folding duplicates together.

        Two extractors legitimately describe the same node from different files
        — a topic is named by a unit descriptor and given its QoS by the
        generated TypeSupport source. Duplicate entities are therefore folded
        into one, taking the union of their attributes; where both supply the
        same attribute the earlier value wins, so the outcome is deterministic
        given a fixed extractor order. Relations are deduplicated by identity.

        Args:
            other: Result to absorb.
        """
        index = {entity.key: position for position, entity in enumerate(self.entities)}
        for entity in other.entities:
            position = index.get(entity.key)
            if position is None:
                index[entity.key] = len(self.entities)
                self.entities.append(entity)
                continue

            existing = self.entities[position]
            merged_attributes = dict(entity.attributes)
            merged_attributes.update(existing.attributes)
            self.entities[position] = replace(existing, attributes=merged_attributes)

        known_relations = {relation.key for relation in self.relations}
        for relation in other.relations:
            if relation.key not in known_relations:
                known_relations.add(relation.key)
                self.relations.append(relation)

    @property
    def is_empty(self) -> bool:
        """Whether nothing at all was extracted."""
        return not self.entities and not self.relations
