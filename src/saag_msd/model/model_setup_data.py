"""
Description: Mandatory-field verification and Model Setup Data assembly rules (SRS MSD.21-23).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from saag_contracts.documents.model_setup_data import (
    ModelSetupDataDocument,
    NodeType,
    Provenance,
)
from saag_contracts.errors.acquisition import AcquisitionError, AcquisitionStatus
from saag_contracts.types.identifiers import SystemVersionRef
from saag_msd.model.extraction import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from saag_msd.model.source_files import SourceFileRecord


@dataclass(frozen=True)
class MandatoryFieldRule:
    """Attributes an entity of a given node type must carry (SRS MSD.21).

    Attributes:
        node_type: Node type the rule applies to.
        required_attributes: Attribute names that must be present and non-empty.
    """

    node_type: NodeType
    required_attributes: tuple[str, ...]

    def missing_attributes(self, entity: ExtractedEntity) -> list[str]:
        """Return the required attributes this entity does not satisfy.

        Args:
            entity: Entity to check.

        Returns:
            Names of missing or blank attributes; empty when the entity passes.
        """
        missing: list[str] = []
        for name in self.required_attributes:
            value = entity.attributes.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
        return missing


@dataclass
class MandatoryFieldPolicy:
    """The configured mandatory-field rules, keyed by node type.

    Attributes:
        rules: Rules applied during verification.
    """

    rules: list[MandatoryFieldRule] = field(default_factory=list)

    def for_node_type(self, node_type: NodeType) -> list[MandatoryFieldRule]:
        """Return the rules applying to one node type.

        Args:
            node_type: Node type to look up.

        Returns:
            Matching rules; empty when the node type is unconstrained.
        """
        return [rule for rule in self.rules if rule.node_type == node_type]


@dataclass
class VerificationOutcome:
    """Result of verifying an extraction result against the field policy.

    Attributes:
        accepted: Entities and relations that passed and may be assembled.
        failures: One error record per rejected entity (SRS MSD.22).
    """

    accepted: ExtractionResult = field(default_factory=ExtractionResult)
    failures: list[AcquisitionError] = field(default_factory=list)


def verify_mandatory_fields(
    extraction: ExtractionResult,
    policy: MandatoryFieldPolicy,
    system_version: SystemVersionRef,
    source_type: str,
    occurred_at: datetime,
) -> VerificationOutcome:
    """Run the mandatory-field-presence check over extracted data (SRS MSD.21-22).

    Entities failing the check are dropped, and every relation touching a
    dropped entity is dropped with them — a relation to a node that will not
    exist is exactly the invalid relationship CSM-01.25 would otherwise have to
    reject downstream.

    Args:
        extraction: Entities and relations to verify.
        policy: Rules to apply.
        system_version: Scope the data was acquired for; supplies the
            project/platform association recorded on each failure.
        source_type: Source type recorded on each failure.
        occurred_at: Error time recorded on each failure.

    Returns:
        The accepted subset plus one failure record per rejected entity.
    """
    outcome = VerificationOutcome()
    rejected_keys: set[tuple[NodeType, str]] = set()

    for entity in extraction.entities:
        missing: list[str] = []
        for rule in policy.for_node_type(entity.node_type):
            missing.extend(rule.missing_attributes(entity))

        if missing:
            rejected_keys.add(entity.key)
            outcome.failures.append(
                AcquisitionError(
                    status=AcquisitionStatus.MISSING_DATA,
                    reason=(
                        f"{entity.node_type.value} '{entity.name}' is missing "
                        f"mandatory field(s): {', '.join(sorted(set(missing)))}"
                    ),
                    source_name=entity.origin,
                    source_type=source_type,
                    platform=system_version.platform,
                    occurred_at=occurred_at,
                    detail=f"system_version={system_version.version}",
                )
            )
        else:
            outcome.accepted.entities.append(entity)

    outcome.accepted.relations = [
        relation
        for relation in extraction.relations
        if not _touches_rejected(relation, rejected_keys)
    ]

    return outcome


def _touches_rejected(
    relation: ExtractedRelation, rejected_keys: set[tuple[NodeType, str]]
) -> bool:
    return (relation.source_type, relation.source_name) in rejected_keys or (
        relation.target_type,
        relation.target_name,
    ) in rejected_keys


def assemble_document(
    system_version: SystemVersionRef,
    accepted: ExtractionResult,
    source_files: list[SourceFileRecord],
    provenance: Provenance,
) -> ModelSetupDataDocument:
    """Assemble the Model Setup Data file from verified data (SRS MSD.23).

    Only data already accepted by verification is passed in; this function adds
    nothing and defaults nothing, so what CSM-01 receives is exactly what
    survived the checks.

    Args:
        system_version: Scope the document is created for.
        accepted: Verified entities and relations.
        source_files: Files the model was derived from.
        provenance: How the document was produced and what it omits.

    Returns:
        The assembled document.
    """
    return ModelSetupDataDocument(
        project=system_version.project.name,
        platform=system_version.platform.name,
        system_version=system_version.version,
        entities=[entity.to_contract() for entity in accepted.entities],
        relations=[relation.to_contract() for relation in accepted.relations],
        source_files=[record.to_contract() for record in source_files],
        provenance=provenance,
    )


def document_file_name(platform: str, produced_at: datetime) -> str:
    """Build the Model Setup Data file name.

    The ``msd_<date>_<platform>.json`` shape is fixed by UXD §4, which shows it
    in the Setup screen's file list.

    Args:
        platform: Platform the document was produced for.
        produced_at: Production timestamp.

    Returns:
        File name, without a directory component.
    """
    return f"msd_{produced_at.date().isoformat()}_{platform}.json"
