"""
Description: Data Validation & Model Setup Data Assembler design element (SRS MSD.21-23).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from msd.src.model.data_source import DataSourceType
from msd.src.model.extraction import ExtractedEntity, ExtractionResult
from msd.src.model.model_setup_data import (
    MandatoryFieldPolicy,
    assemble_document,
    verify_mandatory_fields,
)
from msd.src.model.network_topology import NetworkTopology
from msd.src.model.version_inventory import SoftwareUnitVersion
from msd.src.ports.extraction import (
    CodeGenerationPort,
    ModelWideExtractorPort,
    StructuralExtractorPort,
)
from msd.src.ports.support import ClockPort
from msd.src.use_cases._recording import RunRecorder
from msd.src.use_cases.ingest_source_repository import IngestionResult
from shared.contracts.model_setup_data import (
    ModelSetupDataDocument,
    NodeType,
    Provenance,
)
from shared.errors.acquisition import AcquisitionFailure
from shared.types.identifiers import SystemVersionRef


@dataclass
class AssemblyResult:
    """The assembled document and what had to be left out of it.

    Attributes:
        document: The Model Setup Data document.
        excluded_units: Units left out, mapped to why.
    """

    document: ModelSetupDataDocument
    excluded_units: dict[str, str] = field(default_factory=dict)


@dataclass
class _ExtractionOutcome:
    """What extraction produced and which units it had to drop.

    Attributes:
        result: The entities and relations found.
        excluded_units: Units dropped during generation or extraction, mapped
            to why.
        not_supplied: Node types no source provided data for.
    """

    result: ExtractionResult = field(default_factory=ExtractionResult)
    excluded_units: dict[str, str] = field(default_factory=dict)
    not_supplied: list[NodeType] = field(default_factory=list)


class AssembleModelSetupDataUseCase:
    """Verifies the acquired source data and assembles the Model Setup Data file.

    Deriving the model's entities and relations from the transferred files is
    part of this element rather than a separate one: MSD.21 performs its
    mandatory-field check "within the scope of model construction", which means
    the check runs over model-shaped data, so producing that shape and
    verifying it belong to the same step (SDD §3.1.2).

    Extraction runs in three passes. Code generation first, because the
    generated TypeSupport sources carry topic size and QoS and do not exist in
    the repository. Then the per-unit extractors, then the model-wide ones —
    the system deployment descriptor describes every unit's placement at once
    and must be read against the whole transferred set. A unit whose generation
    or extraction fails is dropped and recorded; the rest still produce a model.
    """

    def __init__(
        self,
        generator: CodeGenerationPort,
        unit_extractors: list[StructuralExtractorPort],
        model_extractors: list[ModelWideExtractorPort],
        mandatory_fields: MandatoryFieldPolicy,
        clock: ClockPort,
    ) -> None:
        """Initialize the use case.

        Args:
            generator: Produces or locates each unit's generated sources.
            unit_extractors: Extractors run per software unit.
            model_extractors: Extractors run once over the whole transferred set.
            mandatory_fields: Rules the extracted data is verified against.
            clock: Supplies error and production times.
        """
        self._generator = generator
        self._unit_extractors = unit_extractors
        self._model_extractors = model_extractors
        self._mandatory_fields = mandatory_fields
        self._clock = clock

    def assemble(
        self,
        system_version: SystemVersionRef,
        ingestion: IngestionResult,
        topology: NetworkTopology | None,
        artifacts: dict[str, dict[str, str]],
        run_id: str,
        recorder: RunRecorder,
    ) -> AssemblyResult:
        """Verify the acquired data and assemble it into the document.

        Args:
            system_version: Scope the document is produced for.
            ingestion: What was transferred, and where.
            topology: Network topology, or None when none was supplied.
            artifacts: Package artifact metadata per software unit.
            run_id: Identifier of the production run.
            recorder: Failure recorder for this run.

        Returns:
            The assembled document and the units left out of it.
        """
        extraction = self.extract(ingestion, topology, recorder)

        verification = verify_mandatory_fields(
            extraction=extraction.result,
            policy=self._mandatory_fields,
            system_version=system_version,
            source_type=DataSourceType.SOURCE_REPOSITORY.value,
            occurred_at=self._clock.now(),
        )
        for failure in verification.failures:
            recorder.record(failure)

        _attach_package_artifacts(verification.accepted, artifacts)

        excluded_units = dict(ingestion.excluded_units)
        excluded_units.update(extraction.excluded_units)

        sources = set(ingestion.sources_used)
        if topology is not None:
            sources.add(topology.source_name)
        sources.update(artifact["source_name"] for artifact in artifacts.values())

        document = assemble_document(
            system_version=system_version,
            accepted=verification.accepted,
            source_files=ingestion.files,
            provenance=Provenance(
                produced_at=self._clock.now(),
                run_id=run_id,
                sources=sorted(sources),
                excluded_units=excluded_units,
                not_supplied=extraction.not_supplied,
            ),
        )

        return AssemblyResult(document=document, excluded_units=excluded_units)

    def extract(
        self,
        ingestion: IngestionResult,
        topology: NetworkTopology | None,
        recorder: RunRecorder,
    ) -> _ExtractionOutcome:
        """Extract everything the Model Setup Data file will carry.

        Args:
            ingestion: What was transferred, and where.
            topology: Network topology, or None when no source supplied one.
            recorder: Failure recorder for this run.

        Returns:
            The extracted entities and relations, exclusions, and the node
            types nothing supplied.
        """
        outcome = _ExtractionOutcome()

        for unit in ingestion.units:
            if not self._generate(unit, ingestion, outcome, recorder):
                continue
            self._extract_unit(unit, ingestion, outcome, recorder)

        self._extract_model_wide(ingestion, outcome, recorder)
        self._add_topology(topology, outcome)
        self._mark_not_supplied(outcome)

        return outcome

    def _generate(
        self,
        unit: SoftwareUnitVersion,
        ingestion: IngestionResult,
        outcome: _ExtractionOutcome,
        recorder: RunRecorder,
    ) -> bool:
        unit_tree = ingestion.unit_trees.get(unit.unit_name)
        if unit_tree is None:
            return False

        generation = self._generator.generate(unit, unit_tree)
        if generation.succeeded:
            return True

        recorder.record_missing(
            reason=generation.reason,
            source_name=_source_of(unit, ingestion),
            source_type=DataSourceType.SOURCE_REPOSITORY.value,
            detail="code generation",
        )
        outcome.excluded_units[unit.unit_name] = generation.reason
        return False

    def _extract_unit(
        self,
        unit: SoftwareUnitVersion,
        ingestion: IngestionResult,
        outcome: _ExtractionOutcome,
        recorder: RunRecorder,
    ) -> None:
        files = ingestion.files_for(unit)
        unit_result = ExtractionResult(
            entities=[
                ExtractedEntity(
                    node_type=NodeType.CSU,
                    name=unit.unit_name,
                    attributes={"version": unit.version, "candidate": unit.is_candidate},
                    origin="version_inventory",
                )
            ]
        )

        for extractor in self._unit_extractors:
            try:
                unit_result.merge(extractor.extract(unit, files))
            except AcquisitionFailure as failure:
                recorder.record_failure(
                    failure,
                    source_name=_source_of(unit, ingestion),
                    source_type=DataSourceType.SOURCE_REPOSITORY.value,
                )
                outcome.excluded_units[unit.unit_name] = failure.reason
                return

        outcome.result.merge(unit_result)

    def _extract_model_wide(
        self,
        ingestion: IngestionResult,
        outcome: _ExtractionOutcome,
        recorder: RunRecorder,
    ) -> None:
        for extractor in self._model_extractors:
            try:
                outcome.result.merge(extractor.extract(ingestion.files))
            except AcquisitionFailure as failure:
                recorder.record_failure(
                    failure,
                    source_name=",".join(ingestion.sources_used),
                    source_type=DataSourceType.SOURCE_REPOSITORY.value,
                )

    def _add_topology(
        self, topology: NetworkTopology | None, outcome: _ExtractionOutcome
    ) -> None:
        if topology is None:
            return

        supplied = ExtractionResult()

        for component in topology.components:
            supplied.entities.append(
                ExtractedEntity(
                    node_type=NodeType.NETWORK_COMPONENT,
                    name=component.name,
                    attributes={"component_type": component.component_type, **component.attributes},
                    origin=topology.source_name,
                )
            )

        # A machine the topology source reports is the same processor unit the
        # deployment descriptor places software on. Merging by name unions the
        # two descriptions instead of producing two nodes for one box.
        for machine in topology.machines:
            supplied.entities.append(
                ExtractedEntity(
                    node_type=NodeType.PROCESSOR_UNIT,
                    name=machine.name,
                    attributes=dict(machine.attributes),
                    origin=topology.source_name,
                )
            )

        outcome.result.merge(supplied)

    def _mark_not_supplied(self, outcome: _ExtractionOutcome) -> None:
        present = {entity.node_type for entity in outcome.result.entities}
        outcome.not_supplied = [
            node_type for node_type in NodeType if node_type not in present
        ]


def _source_of(unit: SoftwareUnitVersion, ingestion: IngestionResult) -> str:
    """Return the repository a unit's files came from, for error attribution."""
    for record in ingestion.files:
        if record.package == unit.unit_name:
            return record.source_name
    return unit.source_name


def _attach_package_artifacts(
    accepted: ExtractionResult, artifacts: dict[str, dict[str, str]]
) -> None:
    """Record each unit's package artifact on its node.

    What a package repository supplied has to survive into the model for MSD.4's
    "managed in a controlled, traceable manner" to mean anything; confirming the
    artifact exists and then dropping it would leave no trace of the repository
    ever having been consulted.

    Args:
        accepted: Verified entities, mutated in place.
        artifacts: Artifact metadata per unit name.
    """
    for position, entity in enumerate(accepted.entities):
        if entity.node_type is not NodeType.CSU:
            continue

        artifact = artifacts.get(entity.name)
        if artifact is None:
            continue

        merged = dict(entity.attributes)
        merged["package_artifact"] = artifact
        accepted.entities[position] = replace(entity, attributes=merged)
