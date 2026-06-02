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
from app.config import BUNDLE_ROOT
from app.jobs.scheduler import setup_scheduler

FRONTEND_DIR = BUNDLE_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield


app = FastAPI(title="Rental Management System", lifespan=lifespan)

app.include_router(leases.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(expenses.router)
app.include_router(owners.router)
app.include_router(tenants.router)
app.include_router(properties.router)
app.include_router(units.router)
app.include_router(reconciliation.router)
app.include_router(stats.router)


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

    API_PREFIXES = (
        "/leases", "/invoices", "/payments", "/expenses",
        "/owners", "/tenants", "/properties", "/units",
        "/reconciliation", "/stats",
    )

    @app.middleware("http")
    async def spa_middleware(request, call_next):
        response = await call_next(request)
        if response.status_code == 404:
            if not request.url.path.startswith(API_PREFIXES):
                index = FRONTEND_DIR / "index.html"
                if index.is_file():
                    return FileResponse(str(index))
        return response
