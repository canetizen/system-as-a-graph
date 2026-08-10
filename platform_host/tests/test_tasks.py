"""
Description: Tests how the host assembles background operations from the installed CSUs.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest
from pelix.constants import OBJECTCLASS
from pelix.framework import FrameworkFactory, create_framework

from saag_contracts.specs.tasks import JOB_QUEUE, TaskProvider
from saag_platform.tasks import InlineJobQueue, TaskGateway

# A process holds one framework, so these tests build and tear down their own.


class _Provider:
    """A CSU publishing one operation, standing in for a real one."""

    def __init__(self, tasks: Mapping[str, Callable[..., Any]]) -> None:
        self._tasks = tasks

    def tasks(self) -> Mapping[str, Callable[..., Any]]:
        return self._tasks


class _BrokenProvider:
    def tasks(self) -> Mapping[str, Callable[..., Any]]:
        raise RuntimeError("this CSU cannot say what it publishes")


@pytest.fixture
def context():
    """A bare framework's context, with no CSU installed."""
    framework = create_framework([], {})
    framework.start()
    try:
        yield framework.get_bundle_context()
    finally:
        framework.stop()
        FrameworkFactory.delete_framework(framework)


def test_the_deferral_service_is_published_for_csus_to_require(context) -> None:
    """A CSU declares a requirement on this specification rather than naming a
    queue technology, so the host must publish it under that exact name."""
    gateway = TaskGateway(database_url=None)
    gateway.attach(context)

    reference = context.get_service_reference(JOB_QUEUE)

    assert reference is not None
    assert JOB_QUEUE in reference.get_property(OBJECTCLASS)


def test_without_storage_an_operation_runs_inline(context) -> None:
    """An unconfigured deployment still performs the work. The CSU cannot tell
    the difference at the call site, which is what keeps a queue from being a
    prerequisite for the CSCI to function."""
    ran: list[dict[str, Any]] = []
    context.register_service(TaskProvider, _Provider({"demo.task": lambda **kw: ran.append(kw)}), {})

    gateway = TaskGateway(database_url=None)
    gateway.attach(context)
    context.get_service(context.get_service_reference(JOB_QUEUE)).defer("demo.task", value=1)

    assert ran == [{"value": 1}]
    assert gateway.app is None


def test_an_unpublished_task_is_refused(context) -> None:
    """Deferring a name no CSU publishes is a wiring mistake, and a queue that
    accepted it would lose the work silently."""
    gateway = TaskGateway(database_url=None)
    gateway.attach(context)
    queue = context.get_service(context.get_service_reference(JOB_QUEUE))

    with pytest.raises(KeyError):
        queue.defer("nobody.publishes.this")


def test_a_broken_provider_does_not_deny_the_others_their_queue(context) -> None:
    """One CSU failing to say what it publishes must not leave the rest of the
    CSCI without a deferral service."""
    context.register_service(TaskProvider, _BrokenProvider(), {})
    context.register_service(TaskProvider, _Provider({"demo.task": lambda **kw: None}), {})

    gateway = TaskGateway(database_url=None)
    gateway.attach(context)

    assert context.get_service_reference(JOB_QUEUE) is not None


def test_detaching_withdraws_the_deferral_service(context) -> None:
    """The service must not outlive the host that backs it, or a CSU would hold a
    queue whose application is gone."""
    gateway = TaskGateway(database_url=None)
    gateway.attach(context)
    gateway.detach()

    assert context.get_service_reference(JOB_QUEUE) is None


def test_the_inline_queue_calls_the_task_it_was_given() -> None:
    """Unit-level counterpart of the wiring tests above, so a failure points at
    the queue rather than at the framework."""
    calls: list[tuple[str, Any]] = []
    queue = InlineJobQueue({"demo.task": lambda **kw: calls.append(("demo.task", kw))})

    queue.defer("demo.task", job_id="j1")

    assert calls == [("demo.task", {"job_id": "j1"})]
