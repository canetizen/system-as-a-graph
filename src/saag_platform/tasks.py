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
from procrastinate import App, PsycopgConnector
from sqlalchemy import create_engine, text

from saag_contracts.specs.tasks import JobQueue, TaskProvider

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

    Unlike the REST edge this does not follow the registry: the worker binds to a
    fully populated application at import time, and a task appearing afterwards
    could not be executed by a worker that has already started. Tasks are
    therefore collected once, and a CSU installed later is picked up by the next
    restart.
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

    @property
    def app(self) -> App | None:
        """The background application, or None when operations run inline."""
        return self._app

    def attach(self, context: BundleContext) -> None:
        """Collect the installed CSUs' tasks and publish the deferral service.

        Args:
            context: Bundle context to collect from and register on.
        """
        for reference in context.get_all_service_references(TaskProvider, None) or []:
            provider = context.get_service(reference)
            try:
                published = dict(provider.tasks())
            # A broken CSU must not deny the others their queue.
            except Exception:
                _LOGGER.exception("Task provider %s published nothing", reference)
                context.unget_service(reference)
                continue
            for name, callable_ in published.items():
                if name in self._tasks:
                    _LOGGER.error("Task %s is published by more than one CSU", name)
                self._tasks[name] = callable_

        if self._database_url:
            self._app = self._build_app(self._database_url)
            queue: JobQueue = DeferredJobQueue(self._app)
        else:
            _LOGGER.warning("No queue storage configured; operations run inline")
            queue = InlineJobQueue(self._tasks)

        self._registration = context.register_service(JobQueue, queue, {})
        _LOGGER.info("Published %d task(s): %s", len(self._tasks), ", ".join(sorted(self._tasks)))

    def detach(self) -> None:
        """Withdraw the deferral service."""
        if self._registration is not None:
            self._registration.unregister()
            self._registration = None
        self._tasks.clear()
        self._app = None

    def _build_app(self, url: str) -> App:
        app = App(connector=PsycopgConnector(conninfo=_connection_info(url)))
        for name, callable_ in self._tasks.items():
            app.task(name=name)(callable_)
        _ensure_schema(url, app)
        return app


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
