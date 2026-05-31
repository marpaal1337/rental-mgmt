from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import expenses, invoices, leases, payments, reconciliation
from app.jobs.scheduler import setup_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield


app = FastAPI(title="Rental Management System", lifespan=lifespan)

app.include_router(leases.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(expenses.router)
app.include_router(reconciliation.router)


@app.get("/")
async def root():
    return {"message": "Rental Management System API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
