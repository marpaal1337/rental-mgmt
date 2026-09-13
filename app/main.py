from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.routers import (
    expenses,
    invoices,
    leases,
    owners,
    payments,
    properties,
    reconciliation,
    stats,
    tenants,
    units,
)
from app.config import BUNDLE_ROOT, ENABLE_SCHEDULER
from app.jobs.scheduler import setup_scheduler, shutdown_scheduler

FRONTEND_DIR = BUNDLE_ROOT / "frontend" / "dist"
API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ENABLE_SCHEDULER:
        setup_scheduler()
    try:
        yield
    finally:
        if ENABLE_SCHEDULER:
            shutdown_scheduler()


app = FastAPI(title="Rental Management System", lifespan=lifespan)

app.include_router(leases.router, prefix=API_PREFIX)
app.include_router(invoices.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(expenses.router, prefix=API_PREFIX)
app.include_router(owners.router, prefix=API_PREFIX)
app.include_router(tenants.router, prefix=API_PREFIX)
app.include_router(properties.router, prefix=API_PREFIX)
app.include_router(units.router, prefix=API_PREFIX)
app.include_router(reconciliation.router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    if FRONTEND_DIR.is_dir():
        index = FRONTEND_DIR / "index.html"
        if index.is_file():
            return FileResponse(str(index))
    return {"message": "Rental Management System API"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")


@app.middleware("http")
async def spa_middleware(request, call_next):
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith(API_PREFIX):
        frontend_root = FRONTEND_DIR.resolve()
        candidate = (FRONTEND_DIR / request.url.path.lstrip("/")).resolve()
        if candidate.is_file() and candidate.is_relative_to(frontend_root):
            return FileResponse(str(candidate))
        index = FRONTEND_DIR / "index.html"
        if index.is_file():
            return FileResponse(str(index))
    return response
