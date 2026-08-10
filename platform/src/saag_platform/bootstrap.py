"""
Description: Startup and shutdown of the component framework hosting the CSUs.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pelix.framework import Bundle, Framework, FrameworkFactory, create_framework

#: Framework property naming which process this framework belongs to. Components
#: that wire themselves differently per process read it; the introspection
#: endpoints report it.
PROFILE_PROPERTY = "saag.profile"

#: Bundle lifecycle states, for reporting a composition in words.
_STATE_NAMES = {
    Bundle.UNINSTALLED: "uninstalled",
    Bundle.INSTALLED: "installed",
    Bundle.RESOLVED: "resolved",
    Bundle.STARTING: "starting",
    Bundle.STOPPING: "stopping",
    Bundle.ACTIVE: "active",
}

#: State reported for a CSU that never became a bundle at all.
FAILED_STATE = "failed"

_LOGGER = logging.getLogger(__name__)


def state_name(state: int) -> str:
    """Return the readable name of a bundle lifecycle state.

    Args:
        state: State as reported by ``Bundle.get_state()``.

    Returns:
        The state's name, or its number as text if unrecognised.
    """
    return _STATE_NAMES.get(state, str(state))


@dataclass
class Composition:
    """What a started framework actually consists of.

    A CSU that could not be installed leaves no bundle behind, so the framework
    alone cannot say it was ever expected. Carrying the failures alongside it is
    what lets a reduced CSCI report itself as reduced instead of looking like one
    that never had that CSU.

    Attributes:
        framework: The started framework.
        failures: Bundle module name to the reason it is not running.
    """

    framework: Framework
    failures: dict[str, str] = field(default_factory=dict)


def framework_properties(profile: str) -> dict[str, Any]:
    """Build the framework properties the installed components configure from.

    The environment is read here, once, and handed to components as framework
    properties instead of each component reading it where it happens to be
    needed. A CSU therefore declares which settings it takes and cannot silently
    acquire a dependency on an environment variable.

    Settings belonging to individual CSUs join this table as those CSUs are
    built; today only the profile is CSCI-wide.

    Args:
        profile: Which process this framework serves, e.g. "api" or "worker".

    Returns:
        Framework properties, ready to pass to ``start_framework``.
    """
    return {PROFILE_PROPERTY: profile}


def start_framework(bundles: list[str], properties: dict[str, Any]) -> Composition:
    """Start a framework with the given bundles installed and started.

    Blocking: installing a bundle imports its CSU and starting it wires that
    CSU's adapters, which may open connections. Callers on an event loop must
    move this off it.

    The first bundle is the framework's own component container and is treated as
    part of the framework: if it cannot start, nothing can, and the exception is
    allowed out. Every CSU after it is installed and started individually, and one
    that fails is recorded and skipped rather than aborting startup — a CSCI
    running without one CSU is a supported configuration (SDD §1 decision 6), and
    refusing to start would turn one broken CSU into an outage of the others. This
    is why the bundles are not handed to the framework as a list: doing so makes
    the first failing import fatal.

    Args:
        bundles: Bundle module names, framework core first.
        properties: Framework properties, from ``framework_properties``.

    Returns:
        The started framework together with the CSUs that are not running.

    Raises:
        ValueError: If a framework is already running in this process. The
            framework factory holds one per process, so an API process and a
            worker process each get their own and neither may hold two.
    """
    core, *csus = bundles
    framework = create_framework([core], properties)
    framework.start()
    context = framework.get_bundle_context()

    failures: dict[str, str] = {}
    for module in csus:
        try:
            context.install_bundle(module).start()
        except Exception as exc:
            failures[module] = f"{type(exc).__name__}: {exc}"
            _LOGGER.exception("CSU bundle %s is not running", module)

    _LOGGER.info(
        "Framework started as profile %r with bundles: %s",
        properties.get(PROFILE_PROPERTY),
        ", ".join(
            f"{bundle.get_symbolic_name()}={state_name(bundle.get_state())}"
            for bundle in context.get_bundles()
        ),
    )
    if failures:
        _LOGGER.warning("CSUs not running: %s", ", ".join(sorted(failures)))
    return Composition(framework=framework, failures=failures)


def stop_framework(framework: Framework) -> None:
    """Stop the framework and release the process-wide factory slot.

    Deleting the framework matters as much as stopping it: the factory holds one
    framework per process, and a stopped-but-undeleted framework makes the next
    start fail.

    Args:
        framework: The framework from ``start_framework``.
    """
    framework.stop()
    FrameworkFactory.delete_framework(framework)
