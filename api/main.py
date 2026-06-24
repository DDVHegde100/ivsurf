"""
IVSURF FastAPI backend.

Run: uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import predict, scan, signals

app = FastAPI(
    title="IVSURF API",
    description="Opening scanner and signal research API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/scan", tags=["scan"])
app.include_router(predict.router, prefix="/predict", tags=["predict"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "ivsurf-api"}
