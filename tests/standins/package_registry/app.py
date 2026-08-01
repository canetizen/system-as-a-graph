"""
Description: Stand-in package repository exposing an artifact search endpoint (EXT-IF-03).
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException

#: File holding the artifacts this registry knows about.
ARTIFACTS_FILE_ENV_VAR = "PACKAGE_REGISTRY_ARTIFACTS"

#: Token the registry expects, so the credential path is exercised rather than
#: assumed. Unset means the registry answers anonymously.
TOKEN_ENV_VAR = "PACKAGE_REGISTRY_TOKEN"

_DEFAULT_ARTIFACTS_FILE = Path(__file__).resolve().parent / "artifacts.json"

app = FastAPI(title="stand-in package registry")


def _artifacts() -> list[dict]:
    path = Path(os.getenv(ARTIFACTS_FILE_ENV_VAR) or _DEFAULT_ARTIFACTS_FILE)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle).get("artifacts", [])


@app.get("/health")
def health():
    """Report that the stand-in registry is up."""
    return {"status": "ok"}


@app.get("/api/artifacts")
def search(name: str, version: str, authorization: str | None = Header(default=None)):
    """Return the artifacts matching a name and version.

    Shaped after the search endpoints Artifactory and Nexus expose: a JSON
    object carrying a list. The adapter reading it is configured with the URL
    and the field names, so the real product can differ on both.

    Raises:
        HTTPException: 401 when a token is required and not presented.
    """
    expected = os.getenv(TOKEN_ENV_VAR)
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="A registry token is required")

    matching = [
        artifact
        for artifact in _artifacts()
        if artifact.get("name") == name and artifact.get("version") == version
    ]
    return {"artifacts": matching}
