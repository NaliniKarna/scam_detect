from fastapi import APIRouter
from pydantic import BaseModel
import json
import os
from datetime import datetime
import uuid

router = APIRouter(prefix="/feedback", tags=["Feedback"])

FEEDBACK_FILE = "feedback.json"

if os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, "r") as f:
        try:
            database = json.load(f)
        except json.JSONDecodeError:
            database = []
else:
    database = []

class Feedback(BaseModel):
    message: str

@router.post("/")
def submit_feedback(payload: Feedback):
    feedback_data = payload.dict()
    feedback_data["timestamp"] = datetime.utcnow().isoformat()
    feedback_data["id"] = str(uuid.uuid4())
    database.append(feedback_data)

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(database, f, indent=4)

    # Convert timestamp to milliseconds for frontend
    ts_ms = int(datetime.fromisoformat(feedback_data["timestamp"]).timestamp() * 1000)

    return {"message": "Feedback submitted", "id": feedback_data["id"], "timestamp": ts_ms}


@router.get("/all")
def get_feedback():
    return database
