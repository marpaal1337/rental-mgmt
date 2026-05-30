from fastapi import FastAPI

app = FastAPI(title="Rental Management System")


@app.get("/")
async def root():
    return {"message": "Rental Management System API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
