"""
Description: Health-endpoint test for the VAE-01 operations panel inbound REST adapter.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from saag_vae_operations_panel.api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health():
    response = client.get("/vae/operations-panel/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "csc": "vae", "csu": "operations_panel"}
