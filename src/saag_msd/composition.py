"""
Description: Composition root wiring MSD's use cases to concrete adapters.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from saag_msd.adapters.build.code_generation import (
    GmakeCodeGenerator,
    PrebuiltCodeGenerator,
)
from saag_msd.adapters.extraction.java_imports import JavaImportExtractor
from saag_msd.adapters.extraction.system_descriptor import SystemDescriptorExtractor
from saag_msd.adapters.extraction.type_support import TypeSupportExtractor
from saag_msd.adapters.extraction.unit_descriptor import UnitDescriptorExtractor
from saag_msd.adapters.factory import AdapterContext, AdapterFactory
from saag_msd.adapters.file.model_setup_data_store import (
    FileModelSetupDataStore,
    output_dir,
)
from saag_msd.adapters.memory import (
    InMemoryAcquisitionErrorRepository,
    InMemoryDataSourceConfigurationRepository,
    InMemoryModelSetupDataRepository,
    InMemoryVersionInventoryRepository,
)
from saag_msd.adapters.postgres.repositories import (
    PostgresAcquisitionErrorRepository,
    PostgresDataSourceConfigurationRepository,
    PostgresModelSetupDataRepository,
    PostgresVersionInventoryRepository,
)
from saag_msd.adapters.postgres.tables import build_engine, create_schema
from saag_msd.adapters.rules_config import RulesConfig, load_rules
from saag_msd.adapters.source_seed import load_seed
from saag_msd.adapters.support import EnvCredentialResolver, SystemClock
from saag_msd.model.data_source import DataSourceRegistry, DataSourceType
from saag_msd.ports.repositories import (
    AcquisitionErrorRepository,
    DataSourceConfigurationRepository,
    ModelSetupDataRepository,
    VersionInventoryRepository,
)
from saag_msd.use_cases.acquire_configuration_data import (
    AcquireConfigurationDataUseCase,
)
from saag_msd.use_cases.acquire_network_topology import AcquireNetworkTopologyUseCase
from saag_msd.use_cases.assemble_model_setup_data import AssembleModelSetupDataUseCase
from saag_msd.use_cases.ingest_source_repository import IngestSourceRepositoryUseCase
from saag_msd.use_cases.manage_data_sources import ManageDataSourcesUseCase
from saag_msd.use_cases.manage_version_inventory import ManageVersionInventoryUseCase
from saag_msd.use_cases.produce_model_setup_data import ProduceModelSetupDataUseCase


@dataclass
class Container:
    """The wired object graph one component serves calls from.

    Attributes:
        rules: Pattern-driven rules every adapter reads its behaviour from.
        data_sources: Data source configuration use case.
        configurations: Repository the configurations live in.
        inventory: Version inventory use case.
        errors: Repository failures are recorded in.
        documents: Repository produced documents are written through.
        workspace: Directory transferred files are copied into.
        factory: Builds one adapter per configured source.
    """

    rules: RulesConfig
    data_sources: ManageDataSourcesUseCase
    configurations: DataSourceConfigurationRepository
    inventory: ManageVersionInventoryUseCase
    errors: AcquisitionErrorRepository
    documents: ModelSetupDataRepository
    workspace: Path
    factory: AdapterFactory

    def registry(self) -> DataSourceRegistry:
        """Build a registry over the currently configured sources."""
        return self.data_sources.registry()

    def configuration_data(self) -> AcquireConfigurationDataUseCase:
        """Build the configuration-data acquisition use case for this call."""
        return AcquireConfigurationDataUseCase(
            self.factory.build_all(
                self.registry(), DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE
            )
        )

    def topology(self) -> AcquireNetworkTopologyUseCase:
        """Build the topology acquisition use case for this call."""
        return AcquireNetworkTopologyUseCase(
            sources=self.factory.build_all(self.registry(), DataSourceType.NETWORK_TOPOLOGY),
            configurations=self.configurations,
        )

    def production(self) -> ProduceModelSetupDataUseCase:
        """Build the full production workflow for this call.

        Adapters are built per call rather than held, so an edited source
        configuration takes effect on the next run without a restart.
        """
        registry = self.registry()
        repositories = self.factory.build_all(registry, DataSourceType.SOURCE_REPOSITORY)

        return ProduceModelSetupDataUseCase(
            inventory=self.inventory,
            ingestion=IngestSourceRepositoryUseCase(
                adapters={adapter.source_name: adapter for adapter in repositories},
                configurations=registry.configurations,
                mandatory_files=self.rules.mandatory_files,
            ),
            assembler=AssembleModelSetupDataUseCase(
                generator=_build_generator(self.rules),
                unit_extractors=[
                    UnitDescriptorExtractor(self.rules.unit_descriptor_extraction),
                    TypeSupportExtractor(self.rules.type_support_extraction),
                    JavaImportExtractor(self.rules.java_import_extraction),
                ],
                model_extractors=[
                    SystemDescriptorExtractor(self.rules.system_descriptor_extraction)
                ],
                mandatory_fields=self.rules.mandatory_fields,
                clock=SystemClock(),
            ),
            topology=self.topology(),
            package_repositories=self.factory.build_all(
                registry, DataSourceType.PACKAGE_REPOSITORY
            ),
            documents=self.documents,
            errors=self.errors,
            clock=SystemClock(),
        )


def build_container(
    *,
    database_url: str | None = None,
    workspace_dir: str | None = None,
    document_dir: str | None = None,
    rules_file: str | None = None,
    source_seed_file: str | None = None,
) -> Container:
    """Wire the object graph from explicit configuration.

    Every setting arrives as an argument rather than being read from the
    environment where it is needed, so what this CSU is configurable by is
    visible in one signature and a test can wire it without touching the
    environment at all.

    Falls back to in-memory repositories when no database is configured. That is
    not a test affordance: a deployment without a database still starts, serves,
    and produces documents, losing only what survives a restart.

    Args:
        database_url: Connection string for the metadata store; None keeps
            everything in memory.
        workspace_dir: Directory transferred files are copied into; None uses a
            temporary directory. Kept separate from every source so generation
            and extraction never write back into one.
        document_dir: Directory produced documents are written to; None uses
            this CSU's default.
        rules_file: Rules file to read; None uses the one shipped with this CSU.
        source_seed_file: Sources a fresh deployment starts with; None means no
            seeding, and an operator configures them through the API instead.

    Returns:
        The wired container.

    Raises:
        FileNotFoundError: If a configured rules or seed file does not exist.
    """
    rules = load_rules(rules_file)
    workspace = Path(workspace_dir or Path(tempfile.gettempdir()) / "saag-msd")
    store = FileModelSetupDataStore(output_dir(document_dir))

    configurations: DataSourceConfigurationRepository
    inventory_repository: VersionInventoryRepository
    errors: AcquisitionErrorRepository
    documents: ModelSetupDataRepository

    if database_url:
        engine = build_engine(database_url)
        create_schema(engine)
        configurations = PostgresDataSourceConfigurationRepository(engine)
        inventory_repository = PostgresVersionInventoryRepository(engine)
        errors = PostgresAcquisitionErrorRepository(engine)
        documents = PostgresModelSetupDataRepository(engine, store)
    else:
        configurations = InMemoryDataSourceConfigurationRepository()
        inventory_repository = InMemoryVersionInventoryRepository()
        errors = InMemoryAcquisitionErrorRepository()
        documents = InMemoryModelSetupDataRepository(store)

    data_sources = ManageDataSourcesUseCase(configurations)
    if source_seed_file:
        data_sources.seed(load_seed(Path(source_seed_file)))

    return Container(
        rules=rules,
        data_sources=data_sources,
        configurations=configurations,
        inventory=ManageVersionInventoryUseCase(inventory_repository),
        errors=errors,
        documents=documents,
        workspace=workspace,
        factory=AdapterFactory(
            AdapterContext(
                workspace=workspace,
                classifier=rules.classifier,
                credentials=EnvCredentialResolver(),
            )
        ),
    )


def _build_generator(rules: RulesConfig):
    """Pick the code generation adapter the rules file asks for.

    ``prebuilt`` consumes sources the repository already carries, for
    environments without the project's build toolchain; ``make`` runs the build.
    The port contract is identical either way.
    """
    settings = rules.code_generation
    if str(settings.get("mode", "prebuilt")).strip().lower() != "make":
        return PrebuiltCodeGenerator()

    return GmakeCodeGenerator(
        command=list(settings.get("command", ["gmake", "regenerate_code"])),
        timeout_seconds=int(settings.get("timeout_seconds", 300)),
    )
