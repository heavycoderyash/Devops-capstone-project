from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import appointments, doctors

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Clinic appointment booking API for the MediSlot DevOps capstone.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Probe and scrape endpoints are excluded so they don't drown out real API traffic in dashboards.
Instrumentator(excluded_handlers=["/health", "/ready", "/metrics"]).instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)

app.include_router(doctors.router)
app.include_router(appointments.router)


@app.get("/", tags=["ops"])
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health", tags=["ops"])
def health():
    """Liveness: the process is up and serving HTTP."""
    return {"status": "UP"}


@app.get("/ready", tags=["ops"])
def ready(db: Session = Depends(get_db)):
    """Readiness: the database is reachable, so we can serve real traffic."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "reason": "database unavailable"})
    return {"status": "READY"}
