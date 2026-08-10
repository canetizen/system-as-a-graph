"""
Description: Automates SDP Increment 1's demo scenario against the assembled CSCI.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from importlib import resources
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from saag_platform.app import app

# SDP Increment 1's demo, as one run: an operator authenticates, selects a scope,
# sees the configured sources, records the inventory and produces Model Setup
# Data. It goes through the CSCI's own REST surface — the only surface an operator
# has — so it exercises the composition rather than any CSU in isolation.
#
# The external systems are the stand-ins: a real directory and a real
# configuration management database are what `compose.dev.yml` brings up, and this
# test skips unless a deployment has been configured to reach them. What it does
# not skip on is the CSCI itself, which is assembled here in-process.

#: Set by a deployment that has the stand-in systems running.
DIRECTORY_VARIABLE = "LDAP_URL"
CMDB_VARIABLE = "STANDIN_CMDB_URL"

#: Where the remaining stand-ins answer. Defaulted to the addresses
#: `compose.dev.yml` publishes, so running the stack is the only setup needed.
GIT_VARIABLE = "STANDIN_GIT_URL"
DEFAULT_GIT_URL = "http://localhost:3002"
PACKAGE_REGISTRY_VARIABLE = "STANDIN_PACKAGE_REGISTRY_URL"
DEFAULT_PACKAGE_REGISTRY_URL = "http://localhost:8100"

#: The scope the stand-in configuration management database is seeded with.
PROJECT = "skyline"
PLATFORM = "avionics"
EFFECTIVE_VERSION = "1.0.0"

#: The account the stand-in directory grants every authorization to.
OPERATOR = "operator"

pytestmark = pytest.mark.skipif(
    os.getenv(DIRECTORY_VARIABLE) is None or os.getenv(CMDB_VARIABLE) is None,
    reason=(
        f"{DIRECTORY_VARIABLE} and {CMDB_VARIABLE} are not set; the stand-in "
        "external systems are not running"
    ),
)


@pytest.fixture
def sources(tmp_path: Path) -> Path:
    """The source configuration a fresh deployment starts from.

    Rewritten to the addresses this test can reach: the stand-in seed names each
    system by its compose service, which resolves only inside that network. What
    is under test is the CSCI, not how a deployment spells an address.
    """
    seed = json.loads(
        (Path(__file__).resolve().parents[1] / "standins" / "sources.json").read_text()
    )
    units = resources.files("saag_msd.testing") / "data"
    git_url = os.getenv(GIT_VARIABLE, DEFAULT_GIT_URL).rstrip("/")
    registry_url = os.getenv(PACKAGE_REGISTRY_VARIABLE, DEFAULT_PACKAGE_REGISTRY_URL)
    for source in seed["sources"]:
        if source["source_type"] == "configuration_management_database":
            source["connection_address"] = os.environ[CMDB_VARIABLE]
        elif source["source_type"] == "network_topology":
            source["connection_address"] = str(units / "ansible")
        elif source["source_type"] == "source_repository":
            source["connection_address"] = f"{git_url}/{source['name']}"
        elif source["source_type"] == "package_repository":
            source["connection_address"] = registry_url
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(seed))
    return path


@pytest.fixture
def csci(sources: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """The assembled CSCI, configured as a deployment would configure it."""
    monkeypatch.setenv("MSD_SOURCE_SEED_FILE", str(sources))
    monkeypatch.setenv("MSD_OUTPUT_DIR", str(tmp_path / "documents"))
    monkeypatch.setenv("MSD_WORKSPACE_DIR", str(tmp_path / "workspace"))
    monkeypatch.setenv("VAE_JWT_SECRET", "an-acceptance-secret-long-enough-for-hmac")
    with TestClient(app) as client:
        yield client


#: How long to wait for a deferred production run, in seconds. Generous: the run
#: clones repositories and reads a package registry, and a slow external system
#: must not read as a failure.
COMPLETION_TIMEOUT = 120.0

#: How often to ask, in seconds.
POLL_INTERVAL = 0.5


def _await_completion(csci: TestClient, headers: dict[str, str], job_id: str) -> dict:
    """Poll a production process until it reaches a terminal state.

    Args:
        csci: The assembled CSCI.
        headers: Authorization for the polling operator.
        job_id: Process to watch.

    Returns:
        The process as last reported.

    Raises:
        AssertionError: If it is still in progress when the timeout elapses.
    """
    deadline = time.monotonic() + COMPLETION_TIMEOUT
    while True:
        job = csci.get(
            f"/vae/operations-panel/production/{job_id}", headers=headers
        ).json()
        if job["status"] != "in_progress":
            return job
        assert time.monotonic() < deadline, f"still in progress after {COMPLETION_TIMEOUT}s"
        time.sleep(POLL_INTERVAL)


def _token(csci: TestClient) -> str:
    response = csci.post(
        "/vae/operations-panel/session",
        json={"username": OPERATOR, "password": OPERATOR},
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_an_operator_produces_model_setup_data_end_to_end(csci: TestClient) -> None:
    """The whole of Increment 1's demo, in the order an operator performs it."""
    headers = {"Authorization": f"Bearer {_token(csci)}"}

    # The scope comes from the configuration management database, with the
    # currently effective version marked (SRS VAE-01.4).
    assert csci.get("/vae/operations-panel/scope/projects", headers=headers).json()[
        "projects"
    ] == [PROJECT]
    versions = csci.get(
        f"/vae/operations-panel/scope/projects/{PROJECT}/platforms/{PLATFORM}/versions",
        headers=headers,
    ).json()
    assert versions["effective_version"] == EFFECTIVE_VERSION

    selected = csci.put(
        "/vae/operations-panel/scope",
        headers=headers,
        json={
            "project": PROJECT,
            "platform": PLATFORM,
            "system_version": EFFECTIVE_VERSION,
        },
    )
    assert selected.status_code == 200, selected.text

    # Every configured source is reported, reachable or not (SRS VAE-01.7).
    snapshot = csci.get(
        "/vae/operations-panel/source-status",
        headers=headers,
        params={"project": PROJECT, "platform": PLATFORM},
    ).json()
    assert snapshot["statuses"], "no source was probed"
    assert snapshot["all_reachable"], [
        (status["source_name"], status["detail"])
        for status in snapshot["statuses"]
        if status["accessibility"] != "reachable"
    ]

    # The inventory has to exist before there is anything to produce from
    # (SRS MSD.14); production reports its absence rather than inventing one.
    recorded = csci.post("/vae/operations-panel/version-inventory", headers=headers)
    assert recorded.status_code == 200, recorded.text
    assert recorded.json()["baseline"], "the configuration database named no software unit"

    started = csci.post("/vae/operations-panel/production", headers=headers, json={})
    assert started.status_code == 202, started.text
    job_id = started.json()["job_id"]

    # Whether the operation is already finished or still in progress depends on
    # the deployment: with queue storage configured a separate worker picks it up,
    # without it the work is done before the call returns. Both reach the same
    # three states, so the demo waits for a terminal one rather than assuming
    # which deployment it is running in (SRS VAE-01.6).
    job = _await_completion(csci, headers, job_id)
    assert job["status"] == "succeeded", job["failure_reason"]
    assert job["entity_count"] > 0
    assert job["relation_count"] > 0

    # The produced file is what CSM-01 will consume over INT-IF-01, and the panel
    # lists it for selection (SRS VAE-01.5).
    listed = csci.get("/vae/operations-panel/model-setup-data", headers=headers).json()
    # Most recent first, and not the only one: a store that survives restarts
    # accumulates every earlier run for the same scope, which is the point of
    # letting the operator choose between them.
    assert listed and listed[0]["run_id"] == job["run_id"], [
        entry["run_id"] for entry in listed
    ]

    document = json.loads(Path(job["file_path"]).read_text())
    assert document["project"] == PROJECT
    assert document["system_version"] == EFFECTIVE_VERSION
    assert document["entities"] and document["relations"]
    assert document["provenance"]["sources"]
