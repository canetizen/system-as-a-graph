"""
Description: Loads MSD's file-classification, mandatory-check, and extraction rules from JSON.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from saag_contracts.documents.model_setup_data import NodeType
from saag_msd.model.model_setup_data import MandatoryFieldPolicy, MandatoryFieldRule
from saag_msd.model.source_files import (
    ClassificationRule,
    FileClassifier,
    MandatoryFilePolicy,
    MandatoryFileRule,
    SourceFileKind,
)

#: Environment variable pointing at a replacement rules file. Air-gapped
#: deployments swap the file rather than rebuilding the image.
RULES_FILE_ENV_VAR = "MSD_RULES_FILE"

_DEFAULT_RULES_FILE = Path(__file__).resolve().parent / "rules.json"


@dataclass(frozen=True)
class RulesConfig:
    """Every pattern-driven rule MSD applies, loaded from one file.

    Nothing here is hard-coded in the adapters: a repository that names its
    files differently, or a generated format that changes shape, is a rules-file
    edit rather than a code change.

    Attributes:
        classifier: Assigns a kind to each transferred file.
        mandatory_files: Files that must be obtained (SRS MSD.19).
        mandatory_fields: Attributes entities must carry (SRS MSD.21).
        java_import_extraction: Settings for the Java import extractor.
        unit_descriptor_extraction: Settings for the unit descriptor extractor.
        type_support_extraction: Settings for the generated TypeSupport extractor.
        system_descriptor_extraction: Settings for the deployment descriptor extractor.
        code_generation: Settings for the code generation adapter.
    """

    classifier: FileClassifier
    mandatory_files: MandatoryFilePolicy
    mandatory_fields: MandatoryFieldPolicy
    java_import_extraction: dict[str, Any]
    unit_descriptor_extraction: dict[str, Any]
    type_support_extraction: dict[str, Any]
    system_descriptor_extraction: dict[str, Any]
    code_generation: dict[str, Any]


def _build(data: dict[str, Any]) -> RulesConfig:
    return RulesConfig(
        classifier=FileClassifier(
            rules=[
                ClassificationRule(
                    pattern=item["pattern"], kind=SourceFileKind(item["kind"])
                )
                for item in data.get("file_classification", [])
            ]
        ),
        mandatory_files=MandatoryFilePolicy(
            rules=[
                MandatoryFileRule(
                    kind=SourceFileKind(item["kind"]),
                    pattern=item["pattern"],
                    per_unit=bool(item.get("per_unit", True)),
                )
                for item in data.get("mandatory_files", [])
            ]
        ),
        mandatory_fields=MandatoryFieldPolicy(
            rules=[
                MandatoryFieldRule(
                    node_type=NodeType(item["node_type"]),
                    required_attributes=tuple(item.get("required_attributes", [])),
                )
                for item in data.get("mandatory_fields", [])
            ]
        ),
        java_import_extraction=dict(data.get("java_import_extraction", {})),
        unit_descriptor_extraction=dict(data.get("unit_descriptor_extraction", {})),
        type_support_extraction=dict(data.get("type_support_extraction", {})),
        system_descriptor_extraction=dict(data.get("system_descriptor_extraction", {})),
        code_generation=dict(data.get("code_generation", {})),
    )


def load_rules(path: str | os.PathLike[str] | None = None) -> RulesConfig:
    """Load the rules file.

    Args:
        path: Rules file the deployment asked for, or None for the one shipped
            with this CSU.

    Returns:
        The parsed rules.

    Raises:
        FileNotFoundError: If the resolved file does not exist.
        TypeError: If the file does not contain a JSON object.
        ValueError: If it names an unknown file kind or node type.
    """
    resolved = Path(path or _DEFAULT_RULES_FILE)
    with resolved.open("r", encoding="utf-8") as rules_file:
        data = json.load(rules_file)

    if not isinstance(data, dict):
        raise TypeError(f"Rules file must contain a JSON object: {resolved}")

    return _build(data)
