"""Spatial analytics API routes for Vercel / external clients."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.spatial.animated import ANIMATIONS
from core.spatial.parametric import list_surfaces
from engine.spatial.heston_surface import heston_iv_surface
from engine.spatial.training_history import synthetic_training_history

router = APIRouter()


class SpatialCatalog(BaseModel):
    surfaces: list[str]
    animations: list[str]
    product: str = "OpenPulse"


class HestonGrid(BaseModel):
    strikes: list[list[float]]
    expiries: list[list[float]]
    iv: list[list[float]]


class TrainingHistoryResponse(BaseModel):
    epoch: list[int]
    train_loss: list[float]
    val_loss: list[float]
    train_mae: list[float]
    val_mae: list[float]


@router.get("/catalog", response_model=SpatialCatalog)
def spatial_catalog():
    """List available 3D spatial assets."""
    return SpatialCatalog(surfaces=list_surfaces(), animations=list(ANIMATIONS.keys()))


@router.get("/heston", response_model=HestonGrid)
def heston_grid(spot: float = 100.0):
    kg, eg, iv = heston_iv_surface(spot=spot)
    return HestonGrid(strikes=kg.tolist(), expiries=eg.tolist(), iv=iv.tolist())


@router.get("/training-history", response_model=TrainingHistoryResponse)
def training_history(epochs: int = Query(40, ge=10, le=200)):
    hist = synthetic_training_history(epochs=epochs)
    return TrainingHistoryResponse(
        epoch=hist["epoch"].tolist(),
        train_loss=hist["train_loss"].tolist(),
        val_loss=hist["val_loss"].tolist(),
        train_mae=hist["train_mae"].tolist(),
        val_mae=hist["val_mae"].tolist(),
    )


@router.get("/surfaces/{name}")
def surface_metadata(name: str):
    from core.spatial.parametric import SURFACES

    if name not in SURFACES:
        raise HTTPException(404, f"Unknown surface '{name}'")
    s = SURFACES[name]
    return {"name": s.name, "formula": s.formula}
