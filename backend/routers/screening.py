"""Screening API endpoints."""

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ScreeningPreset
from backend.services.screening_service import execute_screening

router = APIRouter()


class ScreeningCondition(BaseModel):
    group: int = 1
    field: str
    operator: str
    value: float | list | str | None = None


class ScreeningRequest(BaseModel):
    conditions: list[ScreeningCondition] = []
    group_logic: str = "and"
    sort_by: str = "code"
    sort_order: str = "asc"
    page: int = 1
    per_page: int = 50
    market_segments: list[str] = []
    sectors_33: list[str] = []


class PresetCreate(BaseModel):
    name: str
    conditions_json: str


@router.post("/search")
def search(request: ScreeningRequest, db: Session = Depends(get_db)):
    """Execute screening search."""
    return execute_screening(db, request.model_dump())


@router.get("/presets")
def list_presets(db: Session = Depends(get_db)):
    """List all screening presets."""
    presets = db.query(ScreeningPreset).order_by(ScreeningPreset.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "conditions_json": p.conditions_json,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in presets
    ]


@router.post("/presets")
def create_preset(preset: PresetCreate, db: Session = Depends(get_db)):
    """Save a screening preset."""
    p = ScreeningPreset(name=preset.name, conditions_json=preset.conditions_json)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}


@router.delete("/presets/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    """Delete a screening preset."""
    p = db.get(ScreeningPreset, preset_id)
    if not p:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(p)
    db.commit()
    return {"status": "deleted"}
