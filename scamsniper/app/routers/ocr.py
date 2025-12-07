from fastapi import APIRouter, File, UploadFile
from app.services.ocr_service import ocr_engine
from app.services.ml_model import ml_classifier
from app.services.heuristics import heuristics_engine
from app.services.explain import explain
from app.services.transaction_validator import analyze_transaction_image_text
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/scan")
async def scan_image(file: UploadFile = File(...)):
    if not ocr_engine.available:
        return {"error": "OCR service not available. Ensure easyocr and cv2 dependencies are installed."}

    image_bytes = await file.read()

    # Extract text
    ocr_result = ocr_engine.extract_text(image_bytes)
    extracted_text = ocr_result["text"]

    if not extracted_text:
        return {"error": "No readable text found in image."}

    # Check if image contains transaction-related content
    is_transaction = any(keyword in extracted_text.lower() for keyword in 
                        ["transaction", "receipt", "transfer", "bank", "amount", "$", "currency", 
                         "sender", "recipient", "status", "completed", "pending"])
    
    if is_transaction:
        # Use transaction-specific fraud detection
        fraud_analysis = analyze_transaction_image_text(extracted_text)
        
        status = (
            "scam" if fraud_analysis["risk_score"] >= 80 
            else "suspicious" if fraud_analysis["risk_score"] >= 40 
            else "safe"
        )
        
        return {
            "status": status,
            "score": fraud_analysis["risk_score"],
            "text_extracted": extracted_text,
            "reasons": fraud_analysis["reasons"],
            "detection_type": "transaction_fraud"
        }
    else:
        # Use generic scam classification for non-transaction images
        # ML classify
        pred = ml_classifier.predict(extracted_text)

        # Heuristics
        heur = heuristics_engine(extracted_text)

        # Combine scoring
        total_risk = heur["risk"] + (pred["confidence"] * 50)
        if total_risk > 95:
            total_risk = 95

        status = (
            "scam" if total_risk >= 80 
            else "suspicious" if total_risk >= 40 
            else "safe"
        )

        explanation = explain(pred, heur, None)

        return {
            "status": status,
            "score": round(total_risk, 2),
            "text_extracted": extracted_text,
            "reasons": explanation,
            "detection_type": "general_scam"
        }
