"""
Description: Component bundle publishing the VAE-04 CSU's services into the framework.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from fastapi import APIRouter
from pelix.framework import BundleContext
from pelix.ipopo.decorators import (
    ComponentFactory,
    Instantiate,
    Invalidate,
    Provides,
    Validate,
)
from saag_contracts.specs.api import ApiRouterProvider

from saag_vae_design_evaluator.api.routes import build_router


@ComponentFactory("saag-vae-04-factory")
@Provides(ApiRouterProvider)
@Instantiate("saag-vae-04")
class VaeDesignEvaluatorBundle:
    """This CSU as one framework component (SDD §3.6.4).

    Publishes the CSU's REST endpoints. The design elements behind them, and any
    internal interface the CSU provides, are added here as the CSU is built
    (SDP §2); nothing else in the CSCI has to change when they are.
    """

    def __init__(self) -> None:
        self._router: APIRouter | None = None

    @Validate
    def _validate(self, context: BundleContext) -> None:
        """Wire the CSU and publish its services."""
        self._router = build_router()

    @Invalidate
    def _invalidate(self, context: BundleContext) -> None:
        """Drop the CSU's wiring once its services are withdrawn."""
        self._router = None

    def router(self) -> APIRouter:
        """Return this CSU's router.

        Only reachable through the registered service, which exists solely while
        the component is valid, so the router is never absent here.
        """
        assert self._router is not None
        return self._router
