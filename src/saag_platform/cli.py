"""
Description: Console entry point that serves the CSCI's external REST application.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import os

import uvicorn

#: Bound inside a container, so all interfaces rather than loopback.
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


def serve() -> None:
    """Serve the application on the configured address.

    Single worker by design: the framework factory holds one framework per
    process, so several workers would mean several independent compositions in
    one deployment. Scaling is by process replication with shared storage, not by
    worker count.

    Environment:
        SAAG_HOST: Address to bind; defaults to all interfaces.
        SAAG_PORT: Port to bind; defaults to 8000.
    """
    uvicorn.run(
        "saag_platform.app:app",
        host=os.getenv("SAAG_HOST", DEFAULT_HOST),
        port=int(os.getenv("SAAG_PORT", str(DEFAULT_PORT))),
        workers=1,
    )
