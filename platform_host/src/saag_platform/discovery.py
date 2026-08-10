"""
Description: Discovery of the CSU bundles installed into the component framework.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import os
from importlib.metadata import entry_points

#: Entry-point group each CSU distribution publishes its bundle module under.
BUNDLE_ENTRY_POINT_GROUP = "saag.bundles"

#: Replaces discovery entirely with a comma-separated list of bundle modules.
BUNDLES_ENV_VAR = "SAAG_BUNDLES"

#: Removes named CSUs from an otherwise discovered composition.
BUNDLES_EXCLUDE_ENV_VAR = "SAAG_BUNDLES_EXCLUDE"

#: The framework's own component container, required before any CSU can be
#: instantiated, so it is always installed first.
CORE_BUNDLE = "pelix.ipopo.core"


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def discover_bundles() -> list[str]:
    """Return the bundle modules to install, framework core first.

    Discovery is by installed distribution metadata rather than by a list held
    here: installing a CSU's distribution is the whole act of adding it to the
    CSCI, and uninstalling it the whole act of removing it (SDD §1 decision 6).
    Nothing in the platform names a CSU.

    Because the source is *installed* metadata, a CSU added to a bind-mounted
    development tree appears only after its distribution is reinstalled; editing
    files is not enough.

    Environment:
        SAAG_BUNDLES: Comma-separated bundle modules to install instead of the
            discovered set. Used by tests and by deliberately reduced
            deployments.
        SAAG_BUNDLES_EXCLUDE: Comma-separated entry-point names to leave out of
            an otherwise discovered composition.

    Returns:
        Bundle module names. Order beyond the framework core does not affect
        correctness, since binding follows services appearing rather than
        install order, but it is sorted so startup logs and the generated API
        schema stay comparable between runs.
    """
    override = os.getenv(BUNDLES_ENV_VAR)
    if override:
        return [CORE_BUNDLE, *_split(override)]

    excluded = set(_split(os.getenv(BUNDLES_EXCLUDE_ENV_VAR, "")))
    discovered = sorted(
        (point.name, point.value)
        for point in entry_points(group=BUNDLE_ENTRY_POINT_GROUP)
        if point.name not in excluded
    )
    # Deliberately point.value, not point.load(): letting the framework perform
    # the import is what turns a broken CSU into a bundle that fails to start,
    # with the others unaffected, instead of an import error during discovery.
    return [CORE_BUNDLE, *(value for _, value in discovered)]
