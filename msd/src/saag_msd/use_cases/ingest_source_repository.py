"""
Description: Transfers software unit files from the configured repositories (SRS MSD.17-20).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from saag_contracts.errors.acquisition import AcquisitionFailure
from saag_msd.model.data_source import DataSourceConfiguration, DataSourceType
from saag_msd.model.source_files import MandatoryFilePolicy, SourceFileRecord
from saag_msd.model.source_routing import SourceRouter
from saag_msd.model.version_inventory import SoftwareUnitVersion
from saag_msd.ports.external_sources import SourceCodeRepositoryPort
from saag_msd.use_cases._recording import RunRecorder


@dataclass
class IngestionResult:
    """What one ingestion pass transferred and what it could not.

    Attributes:
        files: Every transferred file, across all repositories.
        units: Units whose files transferred completely.
        excluded_units: Units left out, mapped to why. A unit is excluded when
            it cannot be routed, its transfer fails, or a mandatory file is
            missing — the remaining units still go on to produce a model.
        sources_used: Names of the repositories actually read from.
        unit_trees: Local root of each transferred unit, keyed by unit name.
            Code generation runs against these directories.
    """

    files: list[SourceFileRecord] = field(default_factory=list)
    units: list[SoftwareUnitVersion] = field(default_factory=list)
    excluded_units: dict[str, str] = field(default_factory=dict)
    sources_used: list[str] = field(default_factory=list)
    unit_trees: dict[str, Path] = field(default_factory=dict)

    def files_for(self, unit: SoftwareUnitVersion) -> list[SourceFileRecord]:
        """Return the transferred files belonging to one unit.

        Args:
            unit: Unit to filter by.

        Returns:
            That unit's files, in transfer order.
        """
        return [record for record in self.files if record.package == unit.unit_name]


class IngestSourceRepositoryUseCase:
    """Routes each software unit to a repository and transfers its files.

    Several repositories serve one model, so routing comes first: an explicit
    assignment from the configuration management database wins, otherwise the
    repositories are searched in priority order. One repository failing costs
    only the units it holds — every other unit still transfers, which is what
    keeps a partial result useful.
    """

    def __init__(
        self,
        adapters: dict[str, SourceCodeRepositoryPort],
        configurations: list[DataSourceConfiguration],
        mandatory_files: MandatoryFilePolicy,
    ) -> None:
        """Initialize the use case.

        Args:
            adapters: Repository adapters keyed by configured source name.
            configurations: Configured sources; non-repository types are ignored.
            mandatory_files: Rules the transferred set is checked against.
        """
        self._adapters = adapters
        self._router = SourceRouter(configurations)
        self._mandatory_files = mandatory_files

    def ingest(
        self, units: list[SoftwareUnitVersion], recorder: RunRecorder
    ) -> IngestionResult:
        """Transfer every unit's files and check the mandatory-file rules.

        Args:
            units: Software unit versions to transfer.
            recorder: Failure recorder for this run.

        Returns:
            The transferred files, the units that made it, and the exclusions.
        """
        result = IngestionResult()

        routes, unroutable = self._router.route(units, self._holds)
        for entry in unroutable:
            reason = (
                f"'{entry.unit.versioned_name}' was not found in any configured "
                f"repository (tried: {', '.join(entry.sources_tried) or 'none'})"
            )
            recorder.record_missing(
                reason=reason,
                source_name=",".join(entry.sources_tried),
                source_type=DataSourceType.SOURCE_REPOSITORY.value,
                detail="source routing",
            )
            result.excluded_units[entry.unit.unit_name] = reason

        for route in routes:
            adapter = self._adapters.get(route.configuration.name)
            if adapter is None:
                reason = f"No adapter registered for repository '{route.configuration.name}'"
                recorder.record_missing(
                    reason=reason,
                    source_name=route.configuration.name,
                    source_type=DataSourceType.SOURCE_REPOSITORY.value,
                )
                result.excluded_units[route.unit.unit_name] = reason
                continue

            try:
                transferred = adapter.transfer(route.unit)
            except AcquisitionFailure as failure:
                recorder.record_failure(
                    failure,
                    source_name=route.configuration.name,
                    source_type=DataSourceType.SOURCE_REPOSITORY.value,
                )
                result.excluded_units[route.unit.unit_name] = failure.reason
                continue

            missing = self._mandatory_files.missing_for_unit(route.unit.unit_name, transferred)
            if missing:
                reason = (
                    f"Mandatory file(s) missing for '{route.unit.versioned_name}': "
                    f"{', '.join(rule.pattern for rule in missing)}"
                )
                recorder.record_missing(
                    reason=reason,
                    source_name=route.configuration.name,
                    source_type=DataSourceType.SOURCE_REPOSITORY.value,
                    detail="mandatory file check",
                )
                result.excluded_units[route.unit.unit_name] = reason
                continue

            result.files.extend(transferred)
            result.units.append(route.unit)
            result.unit_trees[route.unit.unit_name] = adapter.local_tree(route.unit)
            if route.configuration.name not in result.sources_used:
                result.sources_used.append(route.configuration.name)

        self._check_model_wide(result, recorder)
        return result

    def _check_model_wide(self, result: IngestionResult, recorder: RunRecorder) -> None:
        for rule in self._mandatory_files.missing_for_model(result.files):
            recorder.record_missing(
                reason=(
                    f"Mandatory model-wide file matching '{rule.pattern}' was not "
                    f"obtained from any repository"
                ),
                source_name=",".join(result.sources_used),
                source_type=DataSourceType.SOURCE_REPOSITORY.value,
                detail="mandatory file check",
            )

    def _holds(
        self, configuration: DataSourceConfiguration, unit: SoftwareUnitVersion
    ) -> bool:
        adapter = self._adapters.get(configuration.name)
        return adapter is not None and adapter.holds(unit)
