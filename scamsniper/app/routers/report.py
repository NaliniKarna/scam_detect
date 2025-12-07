from fastapi import APIRouter
from pydantic import BaseModel
import json
import os
from datetime import datetime
import uuid

router = APIRouter(prefix="/report", tags=["Reports"])

class Report(BaseModel):
    text: str
    category: str = None  # Optional; if not provided, default category will be used

# JSON file path
REPORTS_FILE = "reports.json"

# Load existing reports if file exists
if os.path.exists(REPORTS_FILE):
    with open(REPORTS_FILE, "r") as f:
        try:
            database = json.load(f)
        except json.JSONDecodeError:
            database = []
else:
    database = []

# POST endpoint to add report
@router.post("/")
def report_scam(payload: Report):
    report_data = payload.dict()
    
    # Add timestamp and unique ID
    report_data["timestamp"] = datetime.utcnow().isoformat()
    report_data["id"] = str(uuid.uuid4())
    
    # Set default category if not provided
    if not report_data.get("category"):
        report_data["category"] = "unspecified"
    
    database.append(report_data)

    # Save to JSON file
    with open(REPORTS_FILE, "w") as f:
        json.dump(database, f, indent=4)

    return {"message": "Reported successfully", "report_id": report_data["id"]}

# GET endpoint to view all reports
@router.get("/all")
def view_reports():
    return database

# Optional: GET endpoint to view reports by category
@router.get("/category/{cat}")
def view_reports_by_category(cat: str):
    filtered = [r for r in database if r["category"].lower() == cat.lower()]
    return filtered
