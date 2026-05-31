from fastapi import FastAPI

from app.api.routers import expenses, invoices, leases, payments, reconciliation

app = FastAPI(title="Rental Management System")

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
