from fastapi import APIRouter


def build_router() -> APIRouter:
    """Build this CSU's inbound REST adapter.

    A factory rather than a module-level router: the router is owned by the CSU's
    component and lives exactly as long as it does, so the CSCI's REST surface
    cannot outlast the wiring behind it.

    Returns:
        The router to contribute to the CSCI's external API.
    """
    router = APIRouter(prefix="/frd", tags=["frd"])

    @router.get("/health")
    def health():
        return {"status": "ok", "csc": "frd"}

    return router
