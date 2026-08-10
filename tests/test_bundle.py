"""
Description: Tests that MSD's component publishes the interface INT-IF-01 promises.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import inspect

from pelix.ipopo.constants import HANDLER_PROVIDES, IPOPO_FACTORY_CONTEXT

from saag_contracts.specs.api import API_ROUTER_PROVIDER
from saag_contracts.specs.model_setup_data import (
    CONTRACT_VERSION,
    MODEL_SETUP_DATA_PROVISIONING,
    ModelSetupDataProvisioning,
)
from saag_msd.api.provisioning import ModelSetupDataProvisioningService
from saag_msd.bundle import CONTRACT_VERSION_PROPERTY, MsdBundle

# The consumers of INT-IF-01 are in other distributions and cannot be imported
# here, so what this CSU can check on its own is that it offers everything the
# specification declares, with matching signatures. A method missing or renamed
# would otherwise only surface as an AttributeError in a consumer's process.

SPECIFIED = [
    name
    for name, member in inspect.getmembers(ModelSetupDataProvisioning, inspect.isfunction)
    if not name.startswith("_")
]


def _signature(owner: type, name: str) -> inspect.Signature:
    return inspect.signature(getattr(owner, name))


def test_the_specification_declares_the_methods_the_interface_documents() -> None:
    """Guards the list below against silently becoming empty, which would make
    every other assertion here vacuous."""
    assert sorted(SPECIFIED) == [
        "list_errors",
        "list_model_setup_data_files",
        "list_platforms",
        "list_projects",
        "list_system_versions",
        "probe_sources",
        "produce",
    ]


def test_the_component_offers_every_specified_method() -> None:
    for name in SPECIFIED:
        assert callable(getattr(MsdBundle, name, None)), name


def test_the_component_matches_the_specified_signatures() -> None:
    for name in SPECIFIED:
        assert _signature(MsdBundle, name) == _signature(ModelSetupDataProvisioning, name), name


def test_the_inbound_adapter_matches_the_specified_signatures() -> None:
    """The component delegates to this adapter, so a drift between them would put
    the mismatch one call deeper than the component test can see."""
    for name in SPECIFIED:
        assert _signature(ModelSetupDataProvisioningService, name) == _signature(
            ModelSetupDataProvisioning, name
        ), name


def _factory_context():
    return getattr(MsdBundle, IPOPO_FACTORY_CONTEXT)


def test_the_component_publishes_both_of_its_interfaces() -> None:
    """MSD is reached over two protocols — the registry and REST — and the
    platform finds each by its own specification name.

    Read from the component's own declaration rather than from a running
    framework, so this stays a CSU-level test with no other CSU installed.
    """
    declared = {
        specification
        for specifications, *_ in _factory_context().get_handler(HANDLER_PROVIDES)
        for specification in specifications
    }

    assert declared == {MODEL_SETUP_DATA_PROVISIONING, API_ROUTER_PROVIDER}


def test_the_component_advertises_the_contract_version() -> None:
    """A consumer decides from this property whether it can read the documents
    this provider produces, so it has to be published as a service property, not
    implied by the provider's identity."""
    properties = _factory_context().properties

    assert properties[CONTRACT_VERSION_PROPERTY] == CONTRACT_VERSION


def test_every_setting_is_declared_as_a_property() -> None:
    """The CSU's configuration surface is its property list: anything read from
    the environment further down would be invisible to a deployment."""
    declared = set(_factory_context().properties)

    assert declared == {
        CONTRACT_VERSION_PROPERTY,
        "saag.env.database_url",
        "saag.env.msd_workspace_dir",
        "saag.env.msd_output_dir",
        "saag.env.msd_rules_file",
        "saag.env.msd_source_seed_file",
    }
