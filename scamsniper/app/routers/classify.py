from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ml_model import ml_classifier
from app.services.heuristics import heuristics_engine
from app.services.url_reputation import url_reputation
from app.services.explain import explain

router = APIRouter(prefix="/classify", tags=["Scam Detection"])

class Payload(BaseModel):
    text: str
    url: str | None = None

@router.post("/")
def classify(payload: Payload):
    text = payload.text

    # Model prediction
    ml_pred = ml_classifier.predict(text)

    # Heuristics
    heur = heuristics_engine(text)

    # URL scan
    url_data = url_reputation(payload.url) if payload.url else None

    # Combine score with weighted heuristics (heuristics have higher weight for phishing detection)
    total_risk = 0
    total_risk += heur["risk"]  # Heuristics: 0-100 (now 25-65+ with enhanced rules)
    total_risk += (ml_pred["confidence"] * 30)  # ML model contribution (reduced weight since it's not scam-specific)
    if url_data:
        total_risk += url_data["risk"]

    # Bonus: if heuristics detect multiple scam signals, boost the score
    if len(heur["reasons"]) >= 3:
        total_risk += 15

    # Cap at 95 for realistic high-risk scores (100 looks unreliable)
    if total_risk > 95:
        total_risk = 95

    classification = (
        "scam" if total_risk >= 80 
        else "suspicious" if total_risk >= 40  # Lowered from 40 to catch more suspicious content
        else "safe"
    )

    explanation = explain(ml_pred, heur, url_data)

    return {
        "status": classification,
        "score": round(total_risk, 2),
        "reasons": explanation
    }
