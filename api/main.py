"""
IVSURF FastAPI backend.

Run: uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import auth_enabled, require_api_key
from api.routes import opening_range_ws, predict, scan, signals, universes

app = FastAPI(
    title="IVSURF API",
    description="Opening scanner and signal research API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_protected = [Depends(require_api_key)]

app.include_router(scan.router, prefix="/scan", tags=["scan"], dependencies=_protected)
app.include_router(predict.router, prefix="/predict", tags=["predict"], dependencies=_protected)
app.include_router(signals.router, prefix="/signals", tags=["signals"], dependencies=_protected)
app.include_router(universes.router, prefix="/universes", tags=["universes"], dependencies=_protected)
app.include_router(opening_range_ws.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ivsurf-api",
        "auth": "required" if auth_enabled() else "disabled",
    }
