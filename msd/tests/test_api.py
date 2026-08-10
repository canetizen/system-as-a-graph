from importlib.metadata import entry_points

from fastapi import FastAPI
from fastapi.testclient import TestClient

from saag_msd.api.routes import build_router
from saag_msd.composition import build_container


def test_health_is_served_by_the_csu_router():
    app = FastAPI()
    app.include_router(build_router(build_container()))

    response = TestClient(app).get("/msd/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "csc": "msd"}


def test_the_csu_declares_its_bundle():
    """Installing this distribution is the whole act of adding the CSU to the
    CSCI, so the entry point the platform discovers it by is part of the
    contract, not packaging detail."""
    declared = {point.name: point.value for point in entry_points(group="saag.bundles")}

    assert declared["msd"] == "saag_msd.bundle"
