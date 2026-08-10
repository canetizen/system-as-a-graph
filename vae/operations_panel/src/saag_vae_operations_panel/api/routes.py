"""
Description: Inbound REST adapter of the VAE-01 operations panel CSU.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from fastapi import APIRouter

router = APIRouter(prefix="/vae/operations-panel", tags=["vae-operations-panel"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "vae", "csu": "operations_panel"}
