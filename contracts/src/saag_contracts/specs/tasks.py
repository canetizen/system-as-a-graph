"""
Description: Specifications through which CSUs contribute and defer background operations.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, runtime_checkable

from pelix.constants import Specification

#: Registry name of the task-contributing specification.
TASK_PROVIDER = "saag.platform.task-provider"

#: Registry name of the deferral specification the platform provides.
JOB_QUEUE = "saag.platform.job-queue"


@Specification(TASK_PROVIDER)
@runtime_checkable
class TaskProvider(Protocol):
    """A CSU's long-running operations, registered by the platform's worker.

    Platform-internal plumbing, symmetric with ``ApiRouterProvider``: a process
    may hold only one background-worker application, so the platform owns it and
    each CSU contributes the operations it wants executed there. This keeps the
    queue technology out of every CSU.
    """

    def tasks(self) -> Mapping[str, Callable[..., Any]]:
        """Return this CSU's operations, keyed by task name.

        Task names are persisted in queued work, so a CSU must treat its own
        names as a stable contract and never rename one that may still be
        queued.

        Returns:
            Task name to callable. Callables are invoked in the worker process,
            synchronously, with keyword arguments taken from the deferral.
        """
        ...


@Specification(JOB_QUEUE)
@runtime_checkable
class JobQueue(Protocol):
    """Deferral of a long-running operation, provided by the platform.

    The platform decides whether deferral means enqueueing for the worker or
    running inline — an unconfigured deployment has no queue storage, and the
    CSCI is expected to work in that configuration too (SRS CSM-01.30 concerns
    isolation, not the presence of a broker). A CSU therefore states only that
    an operation should run, never where.
    """

    def defer(self, name: str, **arguments: Any) -> None:
        """Request execution of a named task.

        Args:
            name: Task name as published by some ``TaskProvider``.
            **arguments: Keyword arguments for the task. They cross a storage
                boundary, so only values the queue can serialize may be passed.

        Raises:
            KeyError: If no provider publishes that task name.
        """
        ...
