"""
Description: How the panel behaves when Model Setup Data Generation is not part of the CSCI.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from saag_vae_operations_panel.adapters.msd_gateway import (
    ModelSetupDataUnavailable,
    ServiceModelSetupDataGateway,
)
from saag_vae_operations_panel.api import routes
from saag_vae_operations_panel.testing.panel import build_panel

# The panel requires its provider optionally, so "absent" is a state it has to
# behave well in rather than one it can refuse to start in. These tests pin what
# it does; that the panel stays operable while the provider is away is asserted
# across the CSU boundary, in the CSCI composition test.


@pytest.fixture
def panel_without_provider(users_file: Path):
    """A panel wired to a resolver that finds no provisioning service."""
    return build_panel(users_file, gateway=ServiceModelSetupDataGateway(lambda: None))


def test_the_gateway_reports_absence_rather_than_failing_obscurely() -> None:
    """The distinction the whole degradation rests on: the capability is not
    there, as opposed to something having gone wrong inside it."""
    gateway = ServiceModelSetupDataGateway(lambda: None)

    with pytest.raises(ModelSetupDataUnavailable):
        gateway.list_projects()


def test_the_gateway_reads_the_service_afresh_on_every_call() -> None:
    """The framework replaces the injected reference when the provider restarts,
    so a gateway that captured it once would keep calling a dead object."""
    resolved: list[str] = []

    class _Provider:
        def list_projects(self) -> list[str]:
            return ["skyline"]

    def resolver():
        resolved.append("read")
        return _Provider()

    gateway = ServiceModelSetupDataGateway(resolver)
    gateway.list_projects()
    gateway.list_projects()

    assert resolved == ["read", "read"]


def test_an_affected_endpoint_answers_unavailable_with_a_retry_hint(
    panel_without_provider,
) -> None:
    """Not a server error, which would blame the panel, and not a missing route,
    which would tell the browser the URL never existed."""
    app = FastAPI()
    app.include_router(routes.build_router(panel_without_provider))
    session = panel_without_provider.log_in()

    with TestClient(app) as client:
        response = client.get(
            "/vae/operations-panel/scope/projects",
            headers={"Authorization": f"Bearer {session.token}"},
        )

    assert response.status_code == 503
    assert response.headers["Retry-After"]
    assert "not available" in response.json()["detail"]


def test_an_unaffected_endpoint_keeps_answering(panel_without_provider) -> None:
    """The point of degrading one capability rather than the CSU: everything that
    does not need the absent provider still works."""
    app = FastAPI()
    app.include_router(routes.build_router(panel_without_provider))

    with TestClient(app) as client:
        assert client.get("/vae/operations-panel/health").status_code == 200


def test_the_status_stream_reports_unavailability_and_stays_open(
    panel_without_provider,
) -> None:
    """A stream held across a restart of the provider must recover by itself; a
    stream that ended would make the operator reload to get it back."""

    async def collect() -> list[str]:
        frames: list[str] = []
        stream = routes.source_status_events(
            panel_without_provider, platform=None, interval=0.01
        )
        try:
            async for frame in stream:
                frames.append(frame)
                if len(frames) == 2:
                    return frames
        finally:
            await stream.aclose()
        return frames

    frames = asyncio.run(collect())

    assert len(frames) == 2
    for frame in frames:
        assert frame.startswith("event: unavailable\ndata: ")
        payload = json.loads(frame.split("data: ", 1)[1].strip())
        assert "not available" in payload["detail"]
