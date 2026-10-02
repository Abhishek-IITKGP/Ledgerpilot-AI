from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.ai import router as ai_router
from app.api.routes.approval import router as approval_router
from app.api.routes.investigation import router as investigation_router
from app.logging_config import configure_logging


configure_logging()


app = FastAPI(
    title="FinSight AI API",
    description="Financial discrepancy investigation API",
    version="0.1.0",
)


app.include_router(investigation_router)
app.include_router(ai_router)
app.include_router(approval_router)
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}