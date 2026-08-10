"""
Description: Entry point the background worker process binds its application to.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import logging
import os

from saag_platform.bootstrap import (
    DATABASE_URL_VARIABLE,
    environment_property,
    framework_properties,
    start_framework,
)
from saag_platform.discovery import discover_bundles
from saag_platform.tasks import TaskGateway

#: Profile this process runs the framework under. Components that wire themselves
#: differently outside the request path read it; the REST edge is simply never
#: attached here, which keeps the installed CSU set identical between the two
#: processes rather than making the worker a different deployment.
WORKER_PROFILE = "worker"

_LOGGER = logging.getLogger(__name__)


def _build_app():
    """Boot a framework in this process and assemble the worker's application.

    Runs at import time because the worker command binds to a module attribute
    and expects every task already registered on it. That makes failures here
    startup failures, which is why the composition is logged before returning:
    a worker that came up with a CSU missing would otherwise look like a worker
    with nothing to do.

    Returns:
        The background-operation application, with every installed CSU's tasks
        registered on it.

    Raises:
        RuntimeError: If no queue storage is configured. Unlike the API process,
            a worker without storage has nothing it could ever pick up, so
            starting it would be silently useless.
    """
    database_url = os.getenv(DATABASE_URL_VARIABLE)
    if not database_url:
        raise RuntimeError(
            f"{DATABASE_URL_VARIABLE} is required: the worker executes operations "
            "recorded in the queue's storage and has nowhere to read them from."
        )

    properties = framework_properties(WORKER_PROFILE)
    composition = start_framework(discover_bundles(), properties)
    gateway = TaskGateway(properties[environment_property(DATABASE_URL_VARIABLE)])
    gateway.attach(composition.framework.get_bundle_context())

    if composition.failures:
        _LOGGER.warning(
            "Worker started with CSUs missing, so their operations cannot run: %s",
            ", ".join(sorted(composition.failures)),
        )
    if gateway.app is None:  # pragma: no cover - guarded by the check above
        raise RuntimeError("No background application was built")
    return gateway.app


#: What the worker command binds to.
app = _build_app()
