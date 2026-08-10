"""
Description: Drives MSD's real adapters against real protocols rather than doubles.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from importlib import resources
from pathlib import Path

import pytest
from saag_contracts.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from saag_contracts.types.identifiers import PlatformRef, ProjectRef

from saag_msd.adapters.ansible.network_topology_source import (
    AnsibleNetworkTopologySource,
)
from saag_msd.adapters.git.source_code_repository import GitSourceCodeRepository
from saag_msd.adapters.rest.package_repository import RestPackageRepository
from saag_msd.adapters.rules_config import load_rules
from saag_msd.adapters.sql.configuration_management_database import (
    SqlConfigurationManagementDatabase,
)
from saag_msd.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from saag_msd.model.version_inventory import SoftwareUnitVersion

#: The stand-in assets these tests run against.
#: Fixtures this CSU ships, resolved from the installed distribution. Reaching
#: outside it would tie these tests to this repository's layout, which is exactly
#: what must not happen if MSD is to move to its own (SDD §2.5).
TEST_DATA = Path(str(resources.files("saag_msd.testing") / "data"))

#: Connection string for the stand-in configuration management database. The
#: SQL suite is skipped without it, the way the PostgreSQL suite already is.
CMDB_URL_ENV_VAR = "STANDIN_CMDB_URL"


def _configuration(
    source_type: DataSourceType,
    access_method: AccessMethod,
    address: str,
    parameters: dict | None = None,
    credential: CredentialReference | None = None,
) -> DataSourceConfiguration:
    return DataSourceConfiguration(
        source_type=source_type,
        name="under-test",
        access_method=access_method,
        connection_address=address,
        credential=credential,
        parameters=parameters or {},
    )


# --- EXT-IF-02: the git client, against a real repository -------------------


@pytest.fixture
def git_server(tmp_path: Path) -> Path:
    """A real git repository holding one tagged software unit.

    Served over ``file://`` rather than HTTP: it is the same git client doing
    the same clone, and it needs no server to be running, so this runs
    everywhere including CI.
    """
    unit = TEST_DATA / "source_repository" / "bitbucket-a" / "nav_app_1.2.0"
    work = tmp_path / "work"
    work.mkdir()
    subprocess.run(["cp", "-R", f"{unit}/.", str(work)], check=True)

    def git(*arguments: str) -> None:
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", *arguments],
            cwd=work,
            check=True,
            capture_output=True,
        )

    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "nav_app")
    git("tag", "1.2.0")

    bare = tmp_path / "server" / "nav_app.git"
    bare.parent.mkdir(parents=True)
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(work), str(bare)], check=True, capture_output=True
    )
    return bare.parent


def test_git_adapter_clones_a_tagged_unit(git_server: Path, tmp_path: Path):
    """The adapter fetches exactly the requested tag and records its files."""
    adapter = GitSourceCodeRepository(
        configuration=_configuration(
            DataSourceType.SOURCE_REPOSITORY, AccessMethod.GIT_HTTPS, f"file://{git_server}"
        ),
        workspace=tmp_path / "workspace",
        classifier=load_rules().classifier,
    )
    unit = SoftwareUnitVersion(unit_name="nav_app", version="1.2.0")

    assert adapter.holds(unit) is True
    records = adapter.transfer(unit)

    paths = {record.file_path for record in records}
    assert "src/nav_app.xml" in paths
    assert "generated/NavStateTypeSupport.java" in paths
    # The clone is the files at a version, not a working repository.
    assert not any(path.startswith(".git/") for path in paths)
    assert all(record.source_name == "under-test" for record in records)


def test_git_adapter_reports_a_unit_it_does_not_have(git_server: Path, tmp_path: Path):
    """A miss is quiet, so the router can try the next repository."""
    adapter = GitSourceCodeRepository(
        configuration=_configuration(
            DataSourceType.SOURCE_REPOSITORY, AccessMethod.GIT_HTTPS, f"file://{git_server}"
        ),
        workspace=tmp_path / "workspace",
        classifier=load_rules().classifier,
    )

    assert adapter.holds(SoftwareUnitVersion(unit_name="absent", version="9.9.9")) is False


def test_git_adapter_reports_an_unreachable_server(tmp_path: Path):
    """An address nothing answers at is an access error, not an empty result."""
    adapter = GitSourceCodeRepository(
        configuration=_configuration(
            DataSourceType.SOURCE_REPOSITORY,
            AccessMethod.GIT_HTTPS,
            f"file://{tmp_path / 'nowhere'}",
        ),
        workspace=tmp_path / "workspace",
        classifier=load_rules().classifier,
    )

    with pytest.raises(AcquisitionFailure) as raised:
        adapter.check_access()
    assert raised.value.status is AcquisitionStatus.ACCESS_ERROR


# --- EXT-IF-03: the REST client, against a real HTTP server -----------------


@pytest.fixture
def package_server(tmp_path: Path):
    """A real HTTP server answering artifact lookups from a file."""
    (tmp_path / "artifacts").write_text(
        json.dumps({"artifacts": [{"path": "skyline/nav_app.tar.gz", "checksum": "sha256:1"}]}),
        encoding="utf-8",
    )

    handler = partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def test_rest_adapter_reads_an_artifact_over_http(package_server: str):
    """URL template and field names come from configuration, not from code."""
    adapter = RestPackageRepository(
        _configuration(
            DataSourceType.PACKAGE_REPOSITORY,
            AccessMethod.REST,
            package_server,
            parameters={"path_template": "/artifacts", "results_key": "artifacts"},
        )
    )

    found = adapter.find_artifact(SoftwareUnitVersion(unit_name="nav_app", version="1.2.0"))

    assert found == {
        "name": "nav_app",
        "version": "1.2.0",
        "path": "skyline/nav_app.tar.gz",
        "checksum": "sha256:1",
    }


def test_rest_adapter_reports_an_absent_artifact_as_absent(package_server: str):
    """Nothing found is not a failure — the operator's inventory is simply ahead."""
    adapter = RestPackageRepository(
        _configuration(
            DataSourceType.PACKAGE_REPOSITORY,
            AccessMethod.REST,
            package_server,
            parameters={"path_template": "/missing.json"},
        )
    )

    assert adapter.find_artifact(SoftwareUnitVersion(unit_name="x", version="1")) is None


def test_rest_adapter_reports_an_unreachable_registry():
    """A registry nothing answers at is an access error."""
    adapter = RestPackageRepository(
        _configuration(
            DataSourceType.PACKAGE_REPOSITORY, AccessMethod.REST, "http://127.0.0.1:1"
        )
    )

    with pytest.raises(AcquisitionFailure) as raised:
        adapter.find_artifact(SoftwareUnitVersion(unit_name="x", version="1"))
    assert raised.value.status is AcquisitionStatus.ACCESS_ERROR


# --- EXT-IF-04: the Ansible tree --------------------------------------------


def test_ansible_adapter_reads_machines_and_network_components():
    """Both node kinds come out of the tree, scoped to the platform's group."""
    adapter = AnsibleNetworkTopologySource(
        _configuration(
            DataSourceType.NETWORK_TOPOLOGY, AccessMethod.ANSIBLE, str(TEST_DATA / "ansible")
        )
    )

    topology = adapter.fetch(PlatformRef(ProjectRef("skyline"), "avionics"))

    assert {machine.name for machine in topology.machines} == {"console-1", "console-2"}
    assert {component.name for component in topology.components} == {
        "switch-core-1",
        "switch-core-2",
        "segment-mission",
    }
    console = next(m for m in topology.machines if m.name == "console-1")
    assert console.attributes["cpu_cores"] == "8"
    # Group variables reach every machine of the group.
    assert console.attributes["site"] == "mission-bay"


def test_ansible_adapter_scopes_to_the_platform_group():
    """A tree describing several platforms yields only the one asked for."""
    adapter = AnsibleNetworkTopologySource(
        _configuration(
            DataSourceType.NETWORK_TOPOLOGY, AccessMethod.ANSIBLE, str(TEST_DATA / "ansible")
        )
    )

    topology = adapter.fetch(PlatformRef(ProjectRef("skyline"), "ground-station"))

    assert {machine.name for machine in topology.machines} == {"gs-console-1"}


def test_ansible_adapter_reports_a_missing_tree(tmp_path: Path):
    """A tree that is not mounted is an access error, not an empty topology."""
    adapter = AnsibleNetworkTopologySource(
        _configuration(
            DataSourceType.NETWORK_TOPOLOGY, AccessMethod.ANSIBLE, str(tmp_path / "absent")
        )
    )

    with pytest.raises(AcquisitionFailure) as raised:
        adapter.fetch(PlatformRef(ProjectRef("skyline"), "avionics"))
    assert raised.value.status is AcquisitionStatus.ACCESS_ERROR


# --- EXT-IF-01: the SQL client, against the stand-in database ---------------

pytestmark_sql = pytest.mark.skipif(
    os.getenv(CMDB_URL_ENV_VAR) is None,
    reason=f"{CMDB_URL_ENV_VAR} is not set; the stand-in CM database is not exercised",
)

_CMDB_PARAMETERS = json.loads(
    (TEST_DATA / "cmdb_queries.json").read_text(encoding="utf-8")
)


@pytestmark_sql
def test_sql_adapter_reads_the_configured_queries():
    """The adapter runs the operator's SQL and marks the effective version."""
    adapter = SqlConfigurationManagementDatabase(
        _configuration(
            DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE,
            AccessMethod.SQL,
            os.environ[CMDB_URL_ENV_VAR],
            parameters=_CMDB_PARAMETERS,
        )
    )

    projects = adapter.list_projects()
    assert [project.ref.name for project in projects] == ["skyline"]

    platform = PlatformRef(ProjectRef("skyline"), "avionics")
    versions = adapter.list_system_versions(platform)
    assert {version.ref.version for version in versions} == {"1.0.0", "0.9.0"}
    assert [v.ref.version for v in versions if v.is_effective] == ["1.0.0"]

    units = adapter.list_software_units(platform, "1.0.0")
    assert {unit.unit_name for unit in units} == {
        "system_repo",
        "nav_app",
        "sensor_app",
        "helper_lib",
    }
    assert next(u for u in units if u.unit_name == "nav_app").source_name == "bitbucket-a"


@pytestmark_sql
def test_sql_adapter_reports_an_unconfigured_query():
    """A source with no query for something is missing data, not an empty answer."""
    adapter = SqlConfigurationManagementDatabase(
        _configuration(
            DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE,
            AccessMethod.SQL,
            os.environ[CMDB_URL_ENV_VAR],
            parameters={"queries": {}},
        )
    )

    with pytest.raises(AcquisitionFailure) as raised:
        adapter.list_projects()
    assert raised.value.status is AcquisitionStatus.MISSING_DATA
