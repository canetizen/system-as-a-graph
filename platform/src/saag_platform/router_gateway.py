"""
Description: Mounts and unmounts CSU routers on the CSCI's REST surface as their services come and go.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import logging
import threading

from fastapi import FastAPI
from pelix.constants import SERVICE_ID
from pelix.framework import BundleContext
from pelix.internals.registry import ServiceEvent, ServiceReference
from starlette.routing import BaseRoute

from saag_contracts.specs.api import API_ROUTER_PROVIDER, ApiRouterProvider

_LOGGER = logging.getLogger(__name__)


class RouterGateway:
    """Keeps one FastAPI application in step with the registered CSU routers.

    The CSCI has a single external REST surface but the CSUs behind it are
    installed independently, so the surface is assembled at runtime: each CSU
    registers an ``ApiRouterProvider`` and this gateway mounts it, unmounting it
    again when the service goes away.

    Thread-safety: framework service events arrive on the thread that changed the
    registry, which is not the thread serving requests, so every mutation of the
    application's route table is serialised here.

    Uses two pieces of FastAPI's internals — the objects ``include_router``
    appends, and the private call that invalidates its route caches. Both are
    confined to ``_mount`` and ``_unmount`` so a FastAPI upgrade breaks two
    methods rather than the design, and the framework-composition test exercises
    removal specifically so such a break fails loudly.
    """

    def __init__(self, app: FastAPI) -> None:
        """Bind the gateway to the application it maintains.

        Args:
            app: Application whose route table follows the registry.
        """
        self._app = app
        self._context: BundleContext | None = None
        self._mounted: dict[int, list[BaseRoute]] = {}
        self._lock = threading.Lock()

    def attach(self, context: BundleContext) -> None:
        """Mount everything already registered, then follow later changes.

        The initial sweep is not an optimisation: the bundles are started before
        this gateway exists, so their services are already registered and no
        event will ever announce them.

        Args:
            context: Bundle context to listen on.
        """
        self._context = context
        context.add_service_listener(self, specification=API_ROUTER_PROVIDER)
        for reference in context.get_all_service_references(ApiRouterProvider, None) or []:
            self._mount(reference)

    def detach(self) -> None:
        """Unmount every router and stop following the registry."""
        if self._context is None:
            return
        self._context.remove_service_listener(self)
        for service_id in list(self._mounted):
            self._unmount_by_id(service_id)
        self._context = None

    def service_changed(self, event: ServiceEvent) -> None:
        """React to an ``ApiRouterProvider`` appearing or going away.

        Args:
            event: Framework service event.
        """
        reference = event.get_service_reference()
        kind = event.get_kind()
        if kind == ServiceEvent.REGISTERED:
            self._mount(reference)
        elif kind in (ServiceEvent.UNREGISTERING, ServiceEvent.MODIFIED_ENDMATCH):
            self._unmount_by_id(reference.get_property(SERVICE_ID))

    def _mount(self, reference: ServiceReference) -> None:
        service_id = reference.get_property(SERVICE_ID)
        with self._lock:
            if service_id in self._mounted or self._context is None:
                return
            provider = self._context.get_service(reference)
            try:
                router = provider.router()
            # A broken CSU must not break the edge for the others.
            except Exception:
                _LOGGER.exception("Provider %s did not yield a router", service_id)
                self._context.unget_service(reference)
                return

            before = len(self._app.router.routes)
            self._app.include_router(router)
            self._mounted[service_id] = self._app.router.routes[before:]
            self._invalidate_schema()
            _LOGGER.info("Mounted router %r from service %s", router.prefix, service_id)

    def _unmount_by_id(self, service_id: int) -> None:
        with self._lock:
            mounted = self._mounted.pop(service_id, None)
            if mounted is None:
                return
            for route in mounted:
                if route in self._app.router.routes:
                    self._app.router.routes.remove(route)
            # include_router() bumps the route table's version itself; removing
            # entries by hand does not, and stale caches would keep serving a
            # route whose CSU is gone.
            self._app.router._mark_routes_changed()
            self._invalidate_schema()
            _LOGGER.info("Unmounted router from service %s", service_id)

    def _invalidate_schema(self) -> None:
        # The schema is generated once and cached; dropping it makes the next
        # request regenerate it against the routes actually mounted now.
        self._app.openapi_schema = None
