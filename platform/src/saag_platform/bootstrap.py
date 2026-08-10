"""
Description: Startup and shutdown of the component framework hosting the CSUs.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import logging
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

_LOGGER = logging.getLogger(__name__)


def state_name(state: int) -> str:
    """Return the readable name of a bundle lifecycle state.

    Args:
        state: State as reported by ``Bundle.get_state()``.

    Returns:
        The state's name, or its number as text if unrecognised.
    """
    return _STATE_NAMES.get(state, str(state))


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


def start_framework(bundles: list[str], properties: dict[str, Any]) -> Framework:
    """Start a framework with the given bundles installed and started.

    Blocking: installing a bundle imports its CSU and starting it wires that
    CSU's adapters, which may open connections. Callers on an event loop must
    move this off it.

    A bundle that fails to install or start is logged and skipped rather than
    aborting startup, because a CSCI running without one CSU is a supported
    configuration (SDD §1 decision 6) and refusing to start would make one
    broken CSU an outage of the other nine. The resulting composition is always
    reported, so a silently reduced CSCI is still a visible one.

    Args:
        bundles: Bundle module names, framework core first.
        properties: Framework properties, from ``framework_properties``.

    Returns:
        The started framework.

    Raises:
        ValueError: If a framework is already running in this process. The
            framework factory holds one per process, so an API process and a
            worker process each get their own and neither may hold two.
    """
    framework = create_framework(bundles, properties)
    framework.start()
    context = framework.get_bundle_context()

    for bundle in framework.get_bundles():
        if bundle.get_state() == Bundle.ACTIVE:
            continue
        try:
            bundle.start()
        except Exception:
            _LOGGER.exception("Bundle %s failed to start", bundle.get_symbolic_name())

    _LOGGER.info(
        "Framework started as profile %r with bundles: %s",
        properties.get(PROFILE_PROPERTY),
        ", ".join(
            f"{bundle.get_symbolic_name()}={state_name(bundle.get_state())}"
            for bundle in context.get_bundles()
        ),
    )
    return framework


def stop_framework(framework: Framework) -> None:
    """Stop the framework and release the process-wide factory slot.

    Deleting the framework matters as much as stopping it: the factory holds one
    framework per process, and a stopped-but-undeleted framework makes the next
    start fail.

    Args:
        framework: The framework returned by ``start_framework``.
    """
    framework.stop()
    FrameworkFactory.delete_framework(framework)
