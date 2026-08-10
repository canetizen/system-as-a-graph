"""
Description: Tests that every declared specification carries the registry name it advertises.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import pytest
from pelix.constants import PELIX_SPECIFICATION_FIELD

from saag_contracts.specs import internal_interfaces
from saag_contracts.specs.api import API_ROUTER_PROVIDER, ApiRouterProvider
from saag_contracts.specs.model_setup_data import (
    MODEL_SETUP_DATA_PROVISIONING,
    ModelSetupDataProvisioning,
)
from saag_contracts.specs.tasks import JOB_QUEUE, TASK_PROVIDER, JobQueue, TaskProvider

DECLARED = [
    (ApiRouterProvider, API_ROUTER_PROVIDER),
    (TaskProvider, TASK_PROVIDER),
    (JobQueue, JOB_QUEUE),
    (ModelSetupDataProvisioning, MODEL_SETUP_DATA_PROVISIONING),
]

RESERVED = [
    internal_interfaces.SYNTHETIC_DATA_HANDOFF,
    internal_interfaces.FIELD_RECORDS_HANDOFF,
    internal_interfaces.ANALYTICAL_DATA_HANDOFF,
    internal_interfaces.CORE_SYSTEM_MODEL_ACCESS,
]


@pytest.mark.parametrize(("specification", "name"), DECLARED)
def test_specification_registers_under_its_published_name(specification, name):
    """A consumer looks a service up by the module constant, so the decorator
    must inject exactly that name and nothing else."""
    assert getattr(specification, PELIX_SPECIFICATION_FIELD) == [name]


@pytest.mark.parametrize("name", [name for _, name in DECLARED] + RESERVED)
def test_registry_names_are_unique_and_namespaced(name):
    """Names index the SDD's interface table, so they must stay collision-free
    and recognisable as this CSCI's."""
    all_names = [name for _, name in DECLARED] + RESERVED
    assert name.startswith("saag.")
    assert all_names.count(name) == 1
