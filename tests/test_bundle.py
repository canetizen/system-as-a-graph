"""
Description: Tests what the panel's component requires of the CSCI and publishes to it.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from pelix.ipopo.constants import (
    HANDLER_PROVIDES,
    HANDLER_REQUIRES,
    IPOPO_FACTORY_CONTEXT,
)

from saag_contracts.specs.api import API_ROUTER_PROVIDER
from saag_contracts.specs.model_setup_data import MODEL_SETUP_DATA_PROVISIONING
from saag_contracts.specs.tasks import JOB_QUEUE, TASK_PROVIDER
from saag_vae_operations_panel.adapters.job_queue import PRODUCTION_TASK_NAME
from saag_vae_operations_panel.bundle import VaeOperationsPanelBundle


def _factory_context():
    return getattr(VaeOperationsPanelBundle, IPOPO_FACTORY_CONTEXT)


def _requirements() -> dict[str, tuple[str, bool]]:
    return {
        field: (requirement.specification, requirement.optional)
        for field, requirement in _factory_context().get_handler(HANDLER_REQUIRES).items()
    }


def test_model_setup_data_generation_is_required_optionally() -> None:
    """The decisive property of this component, and the reason it is stated as a
    test rather than left to a code review.

    Requiring the provider outright would invalidate the whole panel whenever
    that CSU restarted, withdrawing even login and leaving a browser holding URLs
    that existed a moment ago. Optional keeps the panel serving and lets it report
    the one affected capability as unavailable.
    """
    specification, optional = _requirements()["_msd"]

    assert specification == MODEL_SETUP_DATA_PROVISIONING
    assert optional is True


def test_the_deferral_service_is_required_outright() -> None:
    """A panel that cannot start a production run has no purpose, and the host
    always provides the service, so degrading here would hide a broken host."""
    specification, optional = _requirements()["_queue"]

    assert specification == JOB_QUEUE
    assert optional is False


def test_the_component_publishes_its_endpoints_and_its_operations() -> None:
    declared = {
        specification
        for specifications, *_ in _factory_context().get_handler(HANDLER_PROVIDES)
        for specification in specifications
    }

    assert declared == {API_ROUTER_PROVIDER, TASK_PROVIDER}


def test_the_production_task_name_is_stable() -> None:
    """The name is recorded in queued work, so changing it would orphan jobs a
    previous release had already accepted."""
    assert PRODUCTION_TASK_NAME == "vae01.produce_model_setup_data"


def test_every_setting_is_declared_as_a_property() -> None:
    """The CSU's configuration surface is its property list: anything read from
    the environment further down would be invisible to a deployment."""
    assert set(_factory_context().properties) == {
        "saag.env.database_url",
        "saag.env.vae_jwt_secret",
        "saag.env.vae_session_minutes",
        "saag.env.vae_source_stream_seconds",
        "saag.env.ldap_url",
        "saag.env.ldap_bind_dn_template",
        "saag.env.ldap_group_search_base",
        "saag.env.ldap_service_bind_dn",
        "saag.env.ldap_service_password",
        "saag.env.ldap_group_authorizations",
    }
