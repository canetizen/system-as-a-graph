"""
Description: Tests that the CSCI composes itself from the installed CSUs and follows them at runtime.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pelix.constants import OBJECTCLASS
from pelix.framework import Bundle, BundleContext

from saag_contracts.specs.api import API_ROUTER_PROVIDER, ApiRouterProvider
from saag_contracts.specs.model_setup_data import MODEL_SETUP_DATA_PROVISIONING
from saag_platform.app import app
from saag_platform.discovery import (
    BUNDLES_ENV_VAR,
    BUNDLES_EXCLUDE_ENV_VAR,
    CORE_BUNDLE,
    discover_bundles,
)

# Cross-CSU by nature: these assert what the CSCI becomes once its CSUs are
# installed, which is why they live here rather than with the platform, whose own
# tests must pass with no CSU installed at all.
#
# The framework factory holds one framework per process, so these tests must run
# one at a time and each must leave the factory empty. Entering the application's
# lifespan starts a framework and leaving it stops and deletes one, which is why
# every test below owns its client rather than sharing a session-wide one.


@pytest.fixture(autouse=True)
def _deployment_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """The minimum configuration a deployment supplies.

    Not test scaffolding: a CSU whose required settings are absent is not
    operable, and the CSCI these tests describe is a configured one. Nothing here
    reaches a real external system — the directory adapter only needs to know
    where the directory would be in order to be constructible.
    """
    monkeypatch.setenv("VAE_JWT_SECRET", "an-integration-secret-long-enough-for-hmac")
    monkeypatch.setenv("LDAP_URL", "ldap://directory.invalid:389")
    monkeypatch.setenv(
        "LDAP_BIND_DN_TEMPLATE", "uid={username},ou=people,dc=saag,dc=local"
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Serve the application with its framework started, then shut both down."""
    with TestClient(app) as running:
        yield running


def _context() -> BundleContext:
    return app.state.framework.get_bundle_context()


def _router_providers() -> list:
    return list(_context().get_all_service_references(ApiRouterProvider, None) or [])


def test_every_declared_bundle_is_installed_and_active(client: TestClient) -> None:
    """A CSU that fails to install or start is skipped rather than fatal, so the
    composition has to be asserted instead of inferred from the process being up."""
    reported = {entry["name"]: entry["state"] for entry in client.get("/platform/bundles").json()["bundles"]}

    for module in discover_bundles():
        assert reported.get(module) == "active", f"{module} is {reported.get(module)}"


def test_the_platform_names_no_csu(client: TestClient) -> None:
    """Discovery is by installed metadata; if the platform ever hardcoded a CSU
    this would still pass by luck, so it asserts the converse: everything running
    was discovered, and nothing discovered is missing."""
    running = {
        bundle.get_symbolic_name()
        for bundle in _context().get_bundles()
        if bundle.get_symbolic_name().startswith("saag_")
    }

    assert running == {module for module in discover_bundles() if module != CORE_BUNDLE}


def test_every_installed_csu_is_operable(client: TestClient) -> None:
    """A bundle being active is not the same as the CSU working.

    A component whose settings are missing, or whose required service is absent,
    stays invalid and publishes nothing — the CSU is then indistinguishable from
    one that was never installed. Asserting bundle state alone hid exactly that
    once, so validity is asserted here directly.
    """
    reported = {
        entry["name"]: entry["state"]
        for entry in client.get("/platform/components").json()["components"]
    }

    assert reported, "no CSU declared a component"
    assert {state for state in reported.values()} == {"valid"}, reported


def test_each_csu_publishes_exactly_one_router(client: TestClient) -> None:
    """Two routers from one CSU would mean two mount points for one component
    lifetime, which the gateway's bookkeeping is not built for."""
    providers = _router_providers()
    owners = [reference.get_bundle().get_symbolic_name() for reference in providers]

    assert len(owners) == len(set(owners))
    for reference in providers:
        assert API_ROUTER_PROVIDER in reference.get_property(OBJECTCLASS)


def test_each_internal_interface_has_one_provider_at_a_stated_version(
    client: TestClient,
) -> None:
    """SDD Table 2 gives each internal interface one provider, and §2.3.1 has that
    provider state its contract version.

    Two providers of one interface would make which one a consumer binds to a
    matter of registration order; a provider without a version leaves a consumer
    unable to tell whether it can read what it is handed.
    """
    published = [
        (specification, entry["contract_version"])
        for entry in client.get("/platform/services").json()["services"]
        for specification in entry["specifications"]
        if specification.startswith("saag.int-if-")
    ]

    assert published, "no internal interface is provided yet"
    names = [specification for specification, _ in published]
    assert len(names) == len(set(names)), names
    for specification, version in published:
        assert version, specification


def test_every_registered_router_is_reachable_and_documented(client: TestClient) -> None:
    """The REST surface is assembled from the registry, so the registry and the
    served surface must agree — asserted without naming a single CSU."""
    documented = client.get("/openapi.json").json()["paths"]

    for reference in _router_providers():
        prefix = _context().get_service(reference).router().prefix
        assert client.get(f"{prefix}/health").status_code == 200
        assert any(path.startswith(prefix) for path in documented), prefix


def test_stopping_one_csu_withdraws_only_its_endpoints(client: TestClient) -> None:
    """The justification for the whole arrangement: a CSU can go away and come
    back at runtime without the rest of the CSCI noticing.

    Also the regression guard for the two pieces of FastAPI internals the gateway
    uses — if an upgrade breaks route removal, this fails rather than the surface
    silently keeping a dead route.
    """
    providers = _router_providers()
    assert len(providers) >= 2, "needs two installed CSUs to tell isolation from luck"

    target, other = providers[0], providers[1]
    target_prefix = _context().get_service(target).router().prefix
    other_prefix = _context().get_service(other).router().prefix
    bundle: Bundle = target.get_bundle()

    bundle.stop()

    assert client.get(f"{target_prefix}/health").status_code == 404
    assert client.get(f"{other_prefix}/health").status_code == 200
    assert not any(
        path.startswith(target_prefix) for path in client.get("/openapi.json").json()["paths"]
    )

    bundle.start()

    assert client.get(f"{target_prefix}/health").status_code == 200
    assert any(
        path.startswith(target_prefix) for path in client.get("/openapi.json").json()["paths"]
    )


def test_the_csci_serves_with_a_single_csu_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """SDP §2 delivers the CSUs one increment at a time, so a reduced composition
    is a supported configuration and not a broken installation."""
    monkeypatch.setenv(BUNDLES_ENV_VAR, "saag_scg.bundle")

    with TestClient(app) as reduced:
        installed = [
            entry["name"]
            for entry in reduced.get("/platform/bundles").json()["bundles"]
            if entry["name"].startswith("saag_")
        ]

        assert installed == ["saag_scg.bundle"]
        assert reduced.get("/health").status_code == 200
        assert reduced.get("/scg/health").status_code == 200
        assert reduced.get("/msd/health").status_code == 404
        assert reduced.get("/openapi.json").status_code == 200


def test_a_consumer_keeps_serving_while_its_provider_is_away(client: TestClient) -> None:
    """The reason the panel requires its provider optionally, asserted across the
    CSU boundary rather than inside either CSU.

    A mandatory requirement would invalidate the consumer whenever the provider
    restarted, withdrawing every one of its endpoints — including the ones that
    have nothing to do with the provider. Here the consumer stays valid and keeps
    serving throughout, and both CSUs are operable again afterwards. What the
    consumer answers on the affected capability is its own business and is
    asserted in its own suite.
    """
    context = _context()
    reference = context.get_service_reference(MODEL_SETUP_DATA_PROVISIONING)
    assert reference is not None, "needs the provider installed"
    provider: Bundle = reference.get_bundle()
    consumer_prefix = "/vae/operations-panel"

    assert client.get(f"{consumer_prefix}/health").status_code == 200

    provider.stop()

    assert client.get(f"{consumer_prefix}/health").status_code == 200
    assert context.get_service_reference(MODEL_SETUP_DATA_PROVISIONING) is None

    provider.start()

    assert context.get_service_reference(MODEL_SETUP_DATA_PROVISIONING) is not None
    assert client.get(f"{consumer_prefix}/health").status_code == 200
    assert {
        entry["state"] for entry in client.get("/platform/components").json()["components"]
    } == {"valid"}


def test_one_unusable_csu_does_not_take_the_csci_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refusing to start because one CSU is broken would make that CSU's problem
    an outage of all the others, which the design does not accept.

    The unusable CSU must still be reported: it leaves no bundle behind, so
    without the recorded failure a CSCI missing a CSU would look exactly like one
    that never declared it.
    """
    monkeypatch.setenv(BUNDLES_ENV_VAR, "saag_scg.bundle,saag_nonexistent.bundle")

    with TestClient(app) as degraded:
        reported = {
            entry["name"]: entry["state"]
            for entry in degraded.get("/platform/bundles").json()["bundles"]
        }

        assert reported["saag_scg.bundle"] == "active"
        assert reported["saag_nonexistent.bundle"] == "failed"
        assert degraded.get("/scg/health").status_code == 200


def test_discovery_honours_the_exclusion_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leaving a CSU out is a deployment decision, expressed by entry-point name
    rather than module path so it reads as the CSU identifier the documents use."""
    monkeypatch.delenv(BUNDLES_ENV_VAR, raising=False)
    monkeypatch.setenv(BUNDLES_EXCLUDE_ENV_VAR, "vae-02,vae-03,vae-04")

    remaining = discover_bundles()

    assert "saag_vae_design_verifier.bundle" not in remaining
    assert "saag_vae_design_analyzer.bundle" not in remaining
    assert "saag_vae_design_evaluator.bundle" not in remaining
    assert "saag_msd.bundle" in remaining
