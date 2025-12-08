from fastapi import APIRouter
from pydantic import BaseModel
import json
import os
from datetime import datetime
import uuid

router = APIRouter(prefix="/scan", tags=["Scans"])

SCANS_FILE = "scans.json"

class Scan(BaseModel):
    type: str
    input: str
    verdict: str
    score: float = 0
    when: int = None  # frontend timestamp in ms (optional)

def load_scans():
    if os.path.exists(SCANS_FILE):
        with open(SCANS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_scans(scans):
    with open(SCANS_FILE, "w") as f:
        json.dump(scans, f, indent=4)

@router.post("/")
def add_scan(payload: Scan):
    database = load_scans()  # Always load fresh
    scan_data = payload.dict()

    # Convert frontend "when" to ISO string
    if scan_data.get("when"):
        scan_data["timestamp"] = datetime.utcfromtimestamp(scan_data["when"]/1000).isoformat()
    else:
        scan_data["timestamp"] = datetime.utcnow().isoformat()

    scan_data["id"] = str(uuid.uuid4())

    # Optional: prevent exact duplicates
    if not any(scan['input'] == scan_data['input'] and scan['timestamp'] == scan_data['timestamp'] for scan in database):
        database.append(scan_data)
        save_scans(database)

    return {"message": "Scan saved successfully", "scan_id": scan_data["id"]}

@router.get("/all")
def get_scans():
    return load_scans()
