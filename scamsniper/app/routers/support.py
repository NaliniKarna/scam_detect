from fastapi import APIRouter, UploadFile, Form
from pydantic import BaseModel
import json, os, uuid
from datetime import datetime

router = APIRouter(prefix="/support", tags=["Support"])
SUPPORT_FILE = "support.json"

if os.path.exists(SUPPORT_FILE):
    with open(SUPPORT_FILE, "r") as f:
        try: database = json.load(f)
        except: database = []
else:
    database = []

class Support(BaseModel):
    text: str
    file: str = None

@router.post("/")
async def add_support(text: str = Form(...), file: UploadFile = None):
    data = {"text": text, "file": file.filename if file else None,
            "when": datetime.utcnow().isoformat(),
            "id": str(uuid.uuid4())}
    database.append(data)
    with open(SUPPORT_FILE, "w") as f:
        json.dump(database, f, indent=4)
    return {"message": "Support ticket submitted", "support_id": data["id"]}

@router.get("/all")
def get_support():
    return database
