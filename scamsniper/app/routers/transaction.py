"""
Transaction fraud detection endpoint.
Validates transaction details and screenshots for forgery/manipulation.
"""
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import json
import logging

from app.services.transaction_validator import validate_transaction_details, analyze_transaction_image_text

try:
    from app.services.ocr_service import ocr_engine
    OCR_AVAILABLE = True
except:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transaction", tags=["Transaction Fraud Detection"])


class TransactionData(BaseModel):
    amount: float
    currency: str
    timestamp: str
    transaction_id: str
    recipient: str
    sender: str
    status: str
    description: str = ""


@router.post("/validate")
def validate_transaction(transaction: TransactionData):
    """
    Validate transaction details for fraud indicators.
    
    Checks for:
    - Invalid transaction ID format
    - Impossible timestamps (future dates)
    - Invalid amounts (negative, zero, unrealistic)
    - Suspicious status
    - Missing critical fields
    """
    result = validate_transaction_details(transaction.dict())
    
    return {
        "status": "suspicious" if result["is_suspicious"] else "legitimate",
        "risk_score": result["risk_score"],
        "reasons": result["reasons"]
    }


@router.post("/check-image")
async def check_transaction_image(
    file: UploadFile = File(...),
    transaction_json: Optional[str] = Form(None)
):
    """
    Check transaction image for forgery/manipulation.
    
    Optional: provide transaction_json with transaction details to cross-validate.
    Format: {"amount": 100, "currency": "USD", "timestamp": "2025-12-07 10:30:00", ...}
    """
    
    if not OCR_AVAILABLE:
        return {
            "status": "error",
            "message": "OCR not available in this deployment",
            "risk_score": None
        }
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text from image
        logger.info(f"Extracting text from image: {file.filename}")
        ocr_result = ocr_engine.extract_text(content)
        
        if not ocr_result or "text" not in ocr_result:
            return {
                "status": "error",
                "message": "Failed to extract text from image",
                "risk_score": None
            }
        
        extracted_text = ocr_result["text"]
        
        # Analyze extracted text for forgery
        image_analysis = analyze_transaction_image_text(extracted_text)
        
        # If transaction JSON provided, validate it too
        combined_score = image_analysis["risk_score"]
        combined_reasons = image_analysis["reasons"].copy()
        
        if transaction_json:
            try:
                txn_data = json.loads(transaction_json)
                txn_analysis = validate_transaction_details(txn_data)
                combined_score = min(combined_score + txn_analysis["risk_score"] // 2, 95)
                combined_reasons.extend(txn_analysis["reasons"])
            except json.JSONDecodeError:
                combined_reasons.append("Invalid transaction JSON provided")
        
        return {
            "status": "suspicious" if combined_score >= 40 else "legitimate",
            "risk_score": combined_score,
            "extracted_text": extracted_text[:500],  # Return first 500 chars
            "reasons": list(set(combined_reasons))  # Remove duplicates
        }
    
    except Exception as e:
        logger.error(f"Error processing transaction image: {e}")
        return {
            "status": "error",
            "message": str(e),
            "risk_score": None
        }
