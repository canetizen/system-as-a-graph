"""
Description: Transferred source file records and the mandatory-file rule (SRS MSD.17-19).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from saag_contracts.documents.model_setup_data import SourceFileEntry


class SourceFileKind(str, Enum):
    """What a transferred file is, as far as MSD is concerned.

    Drives which extractor consumes the file and which mandatory-file rule it
    satisfies. ``OTHER`` covers everything transferred but not interpreted.
    """

    BUILD_DESCRIPTOR = "build_descriptor"
    UNIT_DESCRIPTOR = "unit_descriptor"
    INSTALLATION_SCRIPT = "installation_script"
    RUNTIME_CONFIGURATION = "runtime_configuration"
    SYSTEM_DEPLOYMENT_DESCRIPTOR = "system_deployment_descriptor"
    GENERATED_TYPE_SUPPORT = "generated_type_support"
    SOURCE_CODE = "source_code"
    OTHER = "other"


@dataclass(frozen=True)
class SourceFileRecord:
    """One file obtained from a source repository (SRS MSD.18).

    Attributes:
        file_name: File name.
        file_path: Path of the file relative to its repository root.
        package: Software unit the file belongs to.
        version: Version of that unit.
        updated_at: Update timestamp reported by the source.
        source_name: Configured repository the file came from. Mandatory
            because one model draws files from several repositories, and a
            failure must be attributable to a specific one.
        kind: Classified file kind.
        local_path: Absolute path of the transferred copy MSD can read.
    """

    file_name: str
    file_path: str
    package: str
    version: str
    updated_at: datetime
    source_name: str
    kind: SourceFileKind
    local_path: str

    def to_contract(self) -> SourceFileEntry:
        """Convert to the provenance entry carried in the Model Setup Data file."""
        return SourceFileEntry(
            file_name=self.file_name,
            file_path=self.file_path,
            package=self.package,
            version=self.version,
            updated_at=self.updated_at,
            source_name=self.source_name,
        )


@dataclass(frozen=True)
class ClassificationRule:
    """Maps a path glob to a file kind.

    Attributes:
        pattern: Glob matched against a file's repository-relative path.
        kind: Kind assigned to matching files.
    """

    pattern: str
    kind: SourceFileKind


@dataclass
class FileClassifier:
    """Assigns a kind to each transferred file, first matching rule wins.

    Kept pattern-driven rather than hard-coded so a repository that names its
    files differently is a configuration change, not a code change.

    Attributes:
        rules: Classification rules, in precedence order.
    """

    rules: list[ClassificationRule] = field(default_factory=list)

    def classify(self, file_path: str) -> SourceFileKind:
        """Classify one file.

        Args:
            file_path: Repository-relative path of the file.

        Returns:
            The matching kind, or ``SourceFileKind.OTHER`` when no rule matches.
        """
        for rule in self.rules:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return rule.kind
        return SourceFileKind.OTHER


@dataclass(frozen=True)
class MandatoryFileRule:
    """A file that must be obtained, expressed as a glob (SRS MSD.19, CDR-10).

    Attributes:
        kind: Kind the matching file is classified as.
        pattern: Glob matched against each file's repository-relative path.
        per_unit: True when every software unit must satisfy the rule; False
            when one match anywhere in the model is enough (the system
            deployment descriptor).
    """

    kind: SourceFileKind
    pattern: str
    per_unit: bool = True

    def matches(self, record: SourceFileRecord) -> bool:
        """Whether a transferred file satisfies this rule.

        Args:
            record: The transferred file to test.

        Returns:
            True when the file's path matches the rule's glob.
        """
        return fnmatch.fnmatch(record.file_path, self.pattern)


@dataclass
class MandatoryFilePolicy:
    """The configured set of mandatory-file rules.

    Attributes:
        rules: Rules every transfer is checked against.
    """

    rules: list[MandatoryFileRule] = field(default_factory=list)

    def missing_for_unit(
        self, unit_name: str, records: list[SourceFileRecord]
    ) -> list[MandatoryFileRule]:
        """Return the per-unit rules that unit's transferred files fail to satisfy.

        Args:
            unit_name: Software unit being checked.
            records: Files transferred for that unit.

        Returns:
            Unsatisfied per-unit rules; empty when the unit is complete.
        """
        unit_records = [record for record in records if record.package == unit_name]
        return [
            rule
            for rule in self.rules
            if rule.per_unit and not any(rule.matches(record) for record in unit_records)
        ]

    def missing_for_model(self, records: list[SourceFileRecord]) -> list[MandatoryFileRule]:
        """Return the model-wide rules the whole transfer fails to satisfy.

        Args:
            records: Every file transferred for the model.

        Returns:
            Unsatisfied model-wide rules; empty when the transfer is complete.
        """
        return [
            rule
            for rule in self.rules
            if not rule.per_unit and not any(rule.matches(record) for record in records)
        ]
