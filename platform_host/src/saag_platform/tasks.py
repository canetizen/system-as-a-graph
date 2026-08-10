"""
Description: Owns the CSCI's background-operation application and the deferral service CSUs use.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from pelix.framework import BundleContext
from pelix.internals.registry import ServiceEvent, ServiceReference
from procrastinate import App, PsycopgConnector
from saag_contracts.specs.tasks import TASK_PROVIDER, JobQueue, TaskProvider
from sqlalchemy import create_engine, text

_LOGGER = logging.getLogger(__name__)


def _connection_info(url: str) -> str:
    """Convert a SQLAlchemy URL into the libpq form the connector expects.

    A deployment configures one connection string for everything; SQLAlchemy
    wants its driver in the scheme and libpq does not understand it.

    Args:
        url: SQLAlchemy-style connection URL.

    Returns:
        A libpq connection string.
    """
    return url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


class InlineJobQueue:
    """Runs a requested operation immediately, before ``defer`` returns.

    What an unconfigured deployment gets. The operation still passes through the
    same task callable as a deferred one, so the CSU cannot behave differently
    depending on whether a queue exists — it only loses the ability to observe
    the operation while it is in progress, because it is already finished.
    """

    def __init__(self, tasks: Mapping[str, Callable[..., Any]]) -> None:
        """Bind the queue to the published tasks.

        Args:
            tasks: Task name to callable, as published by the CSUs.
        """
        self._tasks = tasks

    def defer(self, name: str, **arguments: Any) -> None:
        """Run the named task now.

        Args:
            name: Task name.
            **arguments: Keyword arguments for the task.

        Raises:
            KeyError: If no CSU publishes that task name.
        """
        self._tasks[name](**arguments)


class DeferredJobQueue:
    """Hands a requested operation to the worker pool.

    This is what makes an operation's "in progress" state observable: the call
    returns as soon as the job is recorded, a separate process picks it up, and
    the CSU that requested it can report progress until that process finishes.
    Concurrent operations are isolated from one another by the same pool.
    """

    def __init__(self, app: App) -> None:
        """Bind the queue to the background application.

        Args:
            app: The configured background-operation application.
        """
        self._app = app

    def defer(self, name: str, **arguments: Any) -> None:
        """Record the named task for the worker pool.

        Args:
            name: Task name.
            **arguments: Keyword arguments for the task. They are stored, so only
                values the queue can serialize may be passed.

        Raises:
            KeyError: If no CSU publishes that task name.
        """
        with self._app.open():
            self._app.configure_task(name=name).defer(**arguments)


class TaskGateway:
    """Assembles the CSCI's one background-operation application from the CSUs.

    Symmetric with the REST edge and for the same reason: a process holds one
    such application, so the host owns it and each CSU contributes the operations
    it wants executed there. A CSU therefore never names the queue technology,
    and the API process and the worker process agree on the task names by
    construction, because both install the same CSUs.

    Publishes the deferral service **before** collecting tasks, and then follows
    the registry. The order is not incidental: a CSU that requires the deferral
    service is not valid until it exists, and an invalid CSU publishes no tasks —
    so collecting first found nothing and every deferred operation failed with the
    task missing. Registering first makes such a CSU valid, and the listener picks
    up the tasks it then publishes.

    A task added after the worker has begun consuming would still not run in that
    worker, so a CSU installed into a running deployment is picked up at the next
    restart. What this handles is the CSUs installed at startup.
    """

    def __init__(self, database_url: str | None) -> None:
        """Prepare the gateway for a deployment's storage.

        Args:
            database_url: Connection string for the queue's storage; None runs
                operations inline instead.
        """
        self._database_url = database_url
        self._app: App | None = None
        self._tasks: dict[str, Callable[..., Any]] = {}
        self._registration = None
        self._context: BundleContext | None = None

    @property
    def app(self) -> App | None:
        """The background application, or None when operations run inline."""
        return self._app

    @property
    def tasks(self) -> Mapping[str, Callable[..., Any]]:
        """The operations collected from the installed CSUs."""
        return dict(self._tasks)

    def attach(self, context: BundleContext) -> None:
        """Publish the deferral service, then collect the CSUs' operations.

        Args:
            context: Bundle context to register on and collect from.
        """
        self._context = context

        if self._database_url:
            self._app = App(connector=PsycopgConnector(conninfo=_connection_info(self._database_url)))
            _ensure_schema(self._database_url, self._app)
            queue: JobQueue = DeferredJobQueue(self._app)
        else:
            _LOGGER.warning("No queue storage configured; operations run inline")
            # Holds the same dictionary this gateway fills, so a task collected
            # after the service was published is still reachable through it.
            queue = InlineJobQueue(self._tasks)

        self._registration = context.register_service(JobQueue, queue, {})

        context.add_service_listener(self, specification=TASK_PROVIDER)
        for reference in context.get_all_service_references(TaskProvider, None) or []:
            self._collect(reference)

        _LOGGER.info("Published %d task(s): %s", len(self._tasks), ", ".join(sorted(self._tasks)))

    def detach(self) -> None:
        """Withdraw the deferral service and stop following the registry."""
        if self._context is not None:
            self._context.remove_service_listener(self)
            self._context = None
        if self._registration is not None:
            self._registration.unregister()
            self._registration = None
        self._tasks.clear()
        self._app = None

    def service_changed(self, event: ServiceEvent) -> None:
        """Collect a CSU's operations when it starts publishing them.

        A CSU that goes away keeps its tasks registered: work it had already
        accepted is recorded and must still be executable, and a task whose CSU is
        gone fails on its own terms rather than as a missing name.

        Args:
            event: Framework service event.
        """
        if event.get_kind() == ServiceEvent.REGISTERED:
            self._collect(event.get_service_reference())

    def _collect(self, reference: ServiceReference) -> None:
        if self._context is None:
            return
        provider = self._context.get_service(reference)
        try:
            published = dict(provider.tasks())
        # A broken CSU must not deny the others their queue.
        except Exception:
            _LOGGER.exception("Task provider %s published nothing", reference)
            self._context.unget_service(reference)
            return

        for name, callable_ in published.items():
            if name in self._tasks:
                _LOGGER.error("Task %s is published by more than one CSU", name)
                continue
            self._tasks[name] = callable_
            if self._app is not None:
                self._app.task(name=name)(callable_)
            _LOGGER.info("Collected task %s", name)


def _ensure_schema(url: str, app: App) -> None:
    """Create the queue's own tables if they are not already there.

    Created at startup rather than by a separate migration step, matching how the
    CSUs create their schemas. Safe from both the API and the worker process:
    whichever starts first wins and the other finds the tables present.

    Args:
        url: SQLAlchemy-style connection URL.
        app: The application whose schema is applied.
    """
    engine = create_engine(url, pool_pre_ping=True, future=True)
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT to_regclass('public.procrastinate_jobs')")
        ).scalar()

    if exists:
        return

    with app.open():
        app.schema_manager.apply_schema()
