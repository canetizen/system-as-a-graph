"""
Description: Specification a CSU provides so the platform can serve its REST endpoints.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pelix.constants import Specification

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from fastapi import APIRouter

#: Registry name of the specification below.
API_ROUTER_PROVIDER = "saag.platform.api-router-provider"


@Specification(API_ROUTER_PROVIDER)
@runtime_checkable
class ApiRouterProvider(Protocol):
    """A CSU's inbound REST adapter, aggregated by the platform's edge.

    This is platform-internal plumbing rather than one of the SDD's interfaces:
    the CSCI has a single external REST surface, and each CSU contributes its
    own routes to it. Registering the router as a service instead of importing
    it is what lets the edge follow a CSU appearing or disappearing at runtime.

    FastAPI is imported only for typing, so a CSU that serves no REST endpoints
    does not have to depend on it merely to read this contract.
    """

    def router(self) -> APIRouter:
        """Return this CSU's router.

        Called once per registration, while the providing component is valid.
        The returned router is expected to be bound to the component's own
        wiring, so its lifetime is the component's lifetime: the platform
        discards it when the service unregisters rather than caching it.

        Returns:
            The router to mount on the CSCI's external API. Its own prefix
            determines where the CSU's endpoints appear.
        """
        ...
