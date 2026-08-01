"""
Description: TC-VAE01-02 step 3 — the accessibility status stream (SRS VAE-01.7).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vae.operations_panel.src.api import routes
from vae.operations_panel.src.api.dependencies import get_panel_container
from vae.operations_panel.src.model.source_status import Accessibility, SourceStatus
from vae.operations_panel.tests.conftest import FIXED_NOW, build_panel


@pytest.fixture
def streaming_panel(users_file, monkeypatch):
    """A panel reporting one reachable and one unreachable source."""
    monkeypatch.setenv(routes.STREAM_INTERVAL_ENV_VAR, "0.01")

    panel = build_panel(users_file)
    panel.gateway.sources = [
        SourceStatus(
            source_type="source_repository",
            source_name="bitbucket-a",
            accessibility=Accessibility.REACHABLE,
            checked_at=FIXED_NOW,
        ),
        SourceStatus(
            source_type="source_repository",
            source_name="bitbucket-b",
            accessibility=Accessibility.UNREACHABLE,
            checked_at=FIXED_NOW,
            detail="connection refused",
        ),
    ]
    return panel


def _take(panel, count: int) -> list[dict]:
    """Consume ``count`` events from the stream generator.

    The generator is consumed directly rather than over HTTP: it never ends by
    itself, and a test client reading an endless response has no clean way to
    stop.
    """

    async def collect() -> list[dict]:
        events: list[dict] = []
        stream = routes.source_status_events(panel, platform=None)
        try:
            async for frame in stream:
                assert frame.startswith("data: ")
                assert frame.endswith("\n\n")
                events.append(json.loads(frame[len("data: ") : -2]))
                if len(events) == count:
                    return events
        finally:
            await stream.aclose()
        return events

    return asyncio.run(collect())


def test_the_stream_pushes_a_fresh_snapshot_per_event(streaming_panel):
    """Continuous display means the panel pushes, not that the operator refreshes."""
    events = _take(streaming_panel, 2)

    assert len(events) == 2
    for event in events:
        assert event["all_reachable"] is False
        assert {item["source_name"] for item in event["statuses"]} == {
            "bitbucket-a",
            "bitbucket-b",
        }
        assert [item["detail"] for item in event["statuses"] if item["detail"]] == [
            "connection refused"
        ]


def test_every_pushed_snapshot_is_recorded(streaming_panel):
    """The pushed status is traceable afterwards, not only seen once."""
    assert streaming_panel.workflow.latest_source_status() is None

    _take(streaming_panel, 2)

    latest = streaming_panel.workflow.latest_source_status()
    assert latest is not None
    assert len(latest.statuses) == 2


def test_the_stream_refuses_a_token_it_did_not_issue(streaming_panel):
    """The stream is as guarded as every other endpoint, despite the query token."""
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_panel_container] = lambda: streaming_panel

    with TestClient(app) as client:
        response = client.get(
            "/vae/operations-panel/source-status/stream", params={"token": "garbage"}
        )

    assert response.status_code == 401
