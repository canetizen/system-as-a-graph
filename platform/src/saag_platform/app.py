"""
Description: The CSCI's external REST application, assembled from the installed CSUs.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pelix.constants import OBJECTCLASS, SERVICE_ID
from starlette.concurrency import run_in_threadpool

from saag_platform.bootstrap import (
    DATABASE_URL_VARIABLE,
    FAILED_STATE,
    PROFILE_PROPERTY,
    environment_property,
    framework_properties,
    start_framework,
    state_name,
    stop_framework,
)
from saag_platform.discovery import discover_bundles
from saag_platform.router_gateway import RouterGateway
from saag_platform.tasks import TaskGateway

#: Profile this process runs the framework under.
API_PROFILE = "api"

#: Service property a provider advertises its contract version as (SDD §2.3.1).
CONTRACT_VERSION_PROPERTY = "saag.contract.version"


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Hold the component framework open for as long as the application serves.

    Starting the framework imports every installed CSU and lets each one wire its
    adapters, so it is moved off the event loop rather than blocking the first
    request.
    """
    properties = framework_properties(API_PROFILE)
    composition = await run_in_threadpool(start_framework, discover_bundles(), properties)
    context = composition.framework.get_bundle_context()

    # Before the REST edge: a CSU that needs the deferral service is not valid
    # without it, and an invalid CSU has no router to mount yet.
    tasks = TaskGateway(properties.get(environment_property(DATABASE_URL_VARIABLE)))
    await run_in_threadpool(tasks.attach, context)

    routers = RouterGateway(app)
    routers.attach(context)
    app.state.framework = composition.framework
    app.state.failures = composition.failures
    app.state.profile = properties[PROFILE_PROPERTY]
    try:
        yield
    finally:
        routers.detach()
        tasks.detach()
        app.state.framework = None
        await run_in_threadpool(stop_framework, composition.framework)


def create_app() -> FastAPI:
    """Build the CSCI's external REST application.

    The application owns no CSU endpoints of its own. It carries the CSCI-level
    health check and the composition introspection below, and every other route
    is contributed by an installed CSU while its component is valid, so the
    surface reflects what is actually running rather than what was imported.

    Returns:
        The application, with the framework bound to its lifespan.
    """
    app = FastAPI(title="system-as-a-graph API", lifespan=_lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report that the CSCI's edge is serving."""
        return {"status": "ok"}

    @app.get("/platform/bundles")
    def bundles() -> dict[str, Any]:
        """Report the installed CSUs and their lifecycle state.

        A CSU that failed to start is reported here rather than merely logged,
        which is what keeps a reduced composition visible instead of looking like
        a CSCI that never had that CSU.
        """
        framework = app.state.framework
        if framework is None:
            return {"profile": None, "bundles": []}
        running = [
            {
                "id": bundle.get_bundle_id(),
                "name": bundle.get_symbolic_name(),
                "state": state_name(bundle.get_state()),
            }
            for bundle in framework.get_bundle_context().get_bundles()
        ]
        # A CSU that could not be installed left no bundle behind, so it is
        # reported from the recorded failures instead — otherwise a CSCI missing
        # a CSU would be indistinguishable from one that never declared it.
        failed = [
            {"id": None, "name": module, "state": FAILED_STATE, "reason": reason}
            for module, reason in sorted(app.state.failures.items())
        ]
        return {"profile": app.state.profile, "bundles": running + failed}

    @app.get("/platform/services")
    def services() -> dict[str, Any]:
        """Report the registered service specifications and their providers.

        This is the running counterpart of SDD Table 2: an internal interface is
        wired exactly when its specification appears here.
        """
        framework = app.state.framework
        if framework is None:
            return {"services": []}
        context = framework.get_bundle_context()
        references = context.get_all_service_references(None, None) or []
        return {
            "services": [
                {
                    "id": reference.get_property(SERVICE_ID),
                    "specifications": [
                        specification
                        for specification in reference.get_property(OBJECTCLASS)
                        if specification.startswith("saag.")
                    ],
                    "provider": reference.get_bundle().get_symbolic_name(),
                    "contract_version": reference.get_property(CONTRACT_VERSION_PROPERTY),
                }
                for reference in references
                if any(
                    specification.startswith("saag.")
                    for specification in reference.get_property(OBJECTCLASS)
                )
            ]
        }

    return app


#: What ``uvicorn saag_platform.app:app`` serves.
app = create_app()
