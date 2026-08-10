"""
Description: Tests that the INT-IF-01 document survives serialization unchanged.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from saag_contracts.documents.model_setup_data import (
    SCHEMA_VERSION,
    EntityRecord,
    ModelSetupDataDocument,
    NodeType,
    Provenance,
    RelationRecord,
    RelationType,
    SourceFileEntry,
)

# The document crosses INT-IF-01 as a file, so the producing and consuming CSUs
# only ever agree through this schema. It is therefore tested here rather than
# only through a producer's suite: a consumer's repository must be able to rely
# on it without installing the producer.

PRODUCED_AT = datetime(2026, 7, 31, 9, 30, tzinfo=UTC)


def _document() -> ModelSetupDataDocument:
    return ModelSetupDataDocument(
        project="skyline",
        platform="avionics",
        system_version="1.0.0",
        entities=[
            EntityRecord(node_type=NodeType.CSU, name="nav_app", attributes={"version": "1.2.0"}),
            EntityRecord(node_type=NodeType.TOPIC, name="telemetry"),
        ],
        relations=[
            RelationRecord(
                relation_type=RelationType.PUBLISHES,
                source_type=NodeType.CSU,
                source_name="nav_app",
                target_type=NodeType.TOPIC,
                target_name="telemetry",
                attributes={"qos": "reliable"},
            )
        ],
        source_files=[
            SourceFileEntry(
                file_name="install.sh",
                file_path="nav_app/install.sh",
                package="nav_app",
                version="1.2.0",
                updated_at=PRODUCED_AT,
                source_name="gitlab-main",
            )
        ],
        provenance=Provenance(
            produced_at=PRODUCED_AT,
            run_id="run-1",
            sources=["cmdb-primary", "gitlab-main"],
            excluded_units={"sensor_app": "source repository unreachable"},
            not_supplied=[NodeType.NETWORK_COMPONENT],
        ),
    )


def test_a_document_round_trips_through_its_json_shape() -> None:
    """Every field must survive the trip, including the enum-valued and nested
    ones — a silent loss here would look to the consumer like the producer never
    supplied the data."""
    original = _document()

    restored = ModelSetupDataDocument.from_dict(original.to_dict())

    assert restored == original


def test_the_schema_version_is_carried_in_the_document() -> None:
    """A consumer decides whether it can read a document from the document
    itself, not from which provider handed it over (SRS CSM-01.3)."""
    assert _document().to_dict()["schema_version"] == SCHEMA_VERSION


def test_a_document_without_a_version_is_read_as_the_current_one() -> None:
    """The first schema predates the field, so its absence means version one
    rather than an unreadable document."""
    payload = _document().to_dict()
    del payload["schema_version"]

    assert ModelSetupDataDocument.from_dict(payload).schema_version == SCHEMA_VERSION


def test_a_missing_mandatory_field_is_refused() -> None:
    """Silently defaulting a missing scope would produce a Core System Model
    attributed to the wrong project or version."""
    payload = _document().to_dict()
    del payload["system_version"]

    with pytest.raises(KeyError):
        ModelSetupDataDocument.from_dict(payload)


def test_an_unknown_enum_value_is_refused() -> None:
    """A node type this schema version does not define means the document was
    produced against a newer contract, which the consumer must not guess at."""
    payload = _document().to_dict()
    payload["entities"][0]["node_type"] = "quantum_unit"

    with pytest.raises(ValueError, match="quantum_unit"):
        ModelSetupDataDocument.from_dict(payload)
