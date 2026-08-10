from fastapi import FastAPI

from saag_adp.api.routes import router as adp_router
from saag_csm_data_binder.api.routes import router as csm_data_binder_router
from saag_csm_model_manager.api.routes import router as csm_model_manager_router
from saag_frd.api.routes import router as frd_router
from saag_msd.api.routes import router as msd_router
from saag_scg.api.routes import router as scg_router
from saag_vae_design_analyzer.api.routes import router as vae_design_analyzer_router
from saag_vae_design_evaluator.api.routes import router as vae_design_evaluator_router
from saag_vae_design_verifier.api.routes import router as vae_design_verifier_router
from saag_vae_operations_panel.api.routes import router as vae_operations_panel_router

app = FastAPI(title="system-as-a-graph API")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(msd_router)
app.include_router(scg_router)
app.include_router(frd_router)
app.include_router(adp_router)
app.include_router(csm_model_manager_router)
app.include_router(csm_data_binder_router)
app.include_router(vae_operations_panel_router)
app.include_router(vae_design_verifier_router)
app.include_router(vae_design_analyzer_router)
app.include_router(vae_design_evaluator_router)
