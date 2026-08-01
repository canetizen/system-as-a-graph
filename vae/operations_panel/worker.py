"""
Description: Entry point the Procrastinate worker process loads the job queue from.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from vae.operations_panel.src.adapters.procrastinate_app import (
    ensure_schema,
    procrastinate_app,
)

ensure_schema()

#: The application the ``procrastinate ... worker`` command binds to.
app = procrastinate_app()
