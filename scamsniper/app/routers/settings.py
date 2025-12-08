from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

# In-memory storage for now; replace with DB if needed
settings_store: Dict[str, str] = {
    "siteName": "ScamSight",
    "adminEmail": "admin@gmail.com",
    "theme": "dark"
}

class SettingUpdate(BaseModel):
    key: str
    value: str

@router.get("/settings")
async def get_settings():
    """Return all settings"""
    return settings_store

@router.post("/settings")
async def update_setting(update: SettingUpdate):
    """Update a specific setting"""
    if update.key not in settings_store:
        raise HTTPException(status_code=400, detail="Invalid setting key")
    settings_store[update.key] = update.value
    return {"success": True, "key": update.key, "value": update.value}
