from fastapi import FastAPI
from fastapi.testclient import TestClient

from saag_adp.api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health():
    response = client.get("/adp/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "csc": "adp"}
