"""
Transaction fraud detection service.
Analyzes transaction screenshots/images for signs of forgery and manipulation.
"""
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def validate_transaction_details(transaction_data: dict) -> dict:
    """
    Validate transaction details for fraud indicators.
    
    Args:
        transaction_data: {
            "amount": float,
            "currency": str,
            "timestamp": str (ISO format or "YYYY-MM-DD HH:MM:SS"),
            "transaction_id": str,
            "recipient": str,
            "sender": str,
            "status": str,
            "description": str,
            "image_url": str (optional)
        }
    
    Returns:
        {
            "risk_score": 0-95,
            "reasons": [list of fraud indicators],
            "is_suspicious": bool
        }
    """
    score = 0
    reasons = []
    
    if not transaction_data:
        return {"risk_score": 0, "reasons": [], "is_suspicious": False}
    
    # 1️⃣ Check transaction ID format
    txn_id = transaction_data.get("transaction_id", "").strip()
    if txn_id:
        if not validate_transaction_id_format(txn_id):
            score += 25
            reasons.append("Unusual transaction ID format")
        else:
            score -= 5  # Legitimate format
    else:
        score += 15
        reasons.append("Missing transaction ID")
    
    # 2️⃣ Check timestamp validity
    timestamp_str = transaction_data.get("timestamp", "")
    if timestamp_str:
        time_check = validate_timestamp(timestamp_str)
        if not time_check["valid"]:
            score += 30
            reasons.append(time_check["reason"])
        elif time_check["in_future"]:
            score += 40
            reasons.append("Transaction timestamp is in the future (impossible)")
    else:
        score += 10
        reasons.append("Missing transaction timestamp")
    
    # 3️⃣ Check amount validity
    amount = transaction_data.get("amount")
    if amount is not None:
        amount_check = validate_amount(amount)
        if not amount_check["valid"]:
            score += 20
            reasons.append(amount_check["reason"])
    else:
        score += 10
        reasons.append("Missing transaction amount")
    
    # 4️⃣ Check currency format
    currency = transaction_data.get("currency", "").upper()
    valid_currencies = ["USD", "EUR", "GBP", "INR", "AUD", "CAD", "SGD", "JPY", "CNY", "CHF"]
    if currency:
        if currency not in valid_currencies:
            score += 15
            reasons.append(f"Invalid/uncommon currency: {currency}")
    else:
        score += 5
        reasons.append("Missing currency")
    
    # 5️⃣ Check status validity
    status = transaction_data.get("status", "").lower()
    valid_statuses = ["completed", "pending", "processing", "success", "confirmed"]
    if status:
        if status not in valid_statuses:
            score += 20
            reasons.append(f"Suspicious transaction status: {status}")
        # "pending" from past timestamps is suspicious
        if status == "pending" and timestamp_str:
            days_old = get_days_difference(timestamp_str)
            if days_old and days_old > 1:
                score += 25
                reasons.append(f"Transaction pending for {days_old} days (unusual)")
    else:
        score += 15
        reasons.append("Missing transaction status")
    
    # 6️⃣ Check recipient/sender format
    recipient = transaction_data.get("recipient", "").strip()
    sender = transaction_data.get("sender", "").strip()
    
    if recipient:
        if len(recipient) < 2:
            score += 15
            reasons.append("Recipient name too short")
    else:
        score += 10
        reasons.append("Missing recipient")
    
    if sender:
        if len(sender) < 2:
            score += 15
            reasons.append("Sender name too short")
    else:
        score += 10
        reasons.append("Missing sender")
    
    # 7️⃣ Check for common screenshot forgery patterns
    description = transaction_data.get("description", "").lower()
    suspicious_descriptions = [
        "test", "fake", "demo", "screenshot", "edited", "photoshopped",
        "manipulated", "forged", "payment@pending", "processing..."
    ]
    for pattern in suspicious_descriptions:
        if pattern in description:
            score += 20
            reasons.append(f"Suspicious description pattern: '{pattern}'")
            break
    
    # 8️⃣ Cross-validate sender and recipient (can't be same)
    if sender and recipient and sender.lower() == recipient.lower():
        score += 30
        reasons.append("Sender and recipient are the same (impossible transaction)")
    
    # Cap score
    score = min(score, 95)
    score = max(0, score)
    
    return {
        "risk_score": score,
        "reasons": reasons,
        "is_suspicious": score >= 40
    }


def validate_transaction_id_format(txn_id: str) -> bool:
    """
    Validate if transaction ID follows typical formats.
    Real bank transaction IDs usually have:
    - Mix of letters and numbers
    - 8-20 characters long
    - No spaces
    - Professional format (not random looking)
    """
    txn_id = str(txn_id).strip()
    
    # Check length
    if len(txn_id) < 6 or len(txn_id) > 25:
        return False
    
    # Check for spaces
    if " " in txn_id:
        return False
    
    # Should have alphanumeric content (letters/numbers)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', txn_id):
        return False
    
    # Real txn IDs usually have mix of numbers and letters
    has_letter = any(c.isalpha() for c in txn_id)
    has_number = any(c.isdigit() for c in txn_id)
    
    return has_letter and has_number


def validate_timestamp(timestamp_str: str) -> dict:
    """
    Validate if transaction timestamp is realistic.
    Returns: {"valid": bool, "in_future": bool, "reason": str}
    """
    try:
        # Try ISO format first
        if "T" in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            # Try common formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return {"valid": False, "in_future": False, "reason": "Invalid timestamp format"}
        
        # Check if in future
        now = datetime.now()
        if dt > now:
            return {"valid": True, "in_future": True, "reason": "Transaction timestamp is in the future"}
        
        # Check if too old (older than 5 years is suspicious for "recent" transaction claims)
        five_years_ago = now - timedelta(days=365*5)
        if dt < five_years_ago:
            return {"valid": True, "in_future": False, "reason": "Transaction is from 5+ years ago"}
        
        return {"valid": True, "in_future": False, "reason": ""}
    
    except Exception as e:
        logger.warning(f"Timestamp validation error: {e}")
        return {"valid": False, "in_future": False, "reason": "Could not parse timestamp"}


def validate_amount(amount) -> dict:
    """
    Validate if transaction amount is realistic.
    """
    try:
        amount = float(amount)
        
        # Check for negative amount
        if amount < 0:
            return {"valid": False, "reason": "Negative transaction amount"}
        
        # Check for zero amount
        if amount == 0:
            return {"valid": False, "reason": "Zero transaction amount"}
        
        # Check for extremely large amounts (> 1 billion is suspicious without context)
        if amount > 1_000_000_000:
            return {"valid": False, "reason": "Suspiciously large transaction amount"}
        
        # Check for unrealistic decimals (most txns have 0-2 decimals)
        if amount != int(amount):
            decimal_places = len(str(amount).split('.')[-1])
            if decimal_places > 4:
                return {"valid": False, "reason": "Unusual decimal places in amount"}
        
        return {"valid": True, "reason": ""}
    
    except (ValueError, TypeError):
        return {"valid": False, "reason": "Invalid amount format"}


def get_days_difference(timestamp_str: str) -> int | None:
    """
    Get days difference from now.
    Returns None if unable to parse.
    """
    try:
        if "T" in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None
        
        diff = (datetime.now() - dt).days
        return abs(diff)
    except:
        return None


def analyze_transaction_image_text(extracted_text: str) -> dict:
    """
    Analyze text extracted from transaction screenshot using OCR.
    Look for forged/manipulated content.
    
    Args:
        extracted_text: Text extracted from transaction image via OCR
    
    Returns:
        {"risk_score": 0-95, "reasons": [], "is_suspicious": bool}
    """
    score = 0
    reasons = []
    text_lower = extracted_text.lower()
    
    # CRITICAL: Look for editing software artifacts - HIGH WEIGHT (image manipulation = definite fraud)
    editing_artifacts = {
        "photoshop": 50,  # Increased from 25 - this is a critical fraud indicator
        "gimp": 50,       # Increased from 25
        "edited image": 45,
        "manipulated": 60,  # Explicit admission of manipulation
        "layer": 40,
        "undo": 35,
        "crop": 30,
        "blur": 30
    }
    
    for artifact, weight in editing_artifacts.items():
        if artifact in text_lower:
            score += weight
            reasons.append(f"Image editing artifact detected: '{artifact}' (+{weight} points)")
            break
    
    # Look for explicit manipulation claims - VERY HIGH WEIGHT
    manipulation_claims = {
        "this image has been manipulated": 70,
        "image has been modified": 65,
        "fake transaction": 75,
        "not a real transaction": 70,
        "photoshopped": 60,
    }
    
    for claim, weight in manipulation_claims.items():
        if claim in text_lower:
            score += weight
            reasons.append(f"Explicit fraud claim detected: '{claim}' (+{weight} points)")
            break
    
    # Look for suspicious phrases - MEDIUM-HIGH WEIGHT
    suspicious_phrases = {
        "this is a test": 50,  # Increased from 30
        "fake": 55,
        "demo": 50,
        "sample": 45,
        "screenshot only": 45,
        "not real": 60,
        "edited": 45,
        "for demonstration": 50
    }
    
    for phrase, weight in suspicious_phrases.items():
        if phrase in text_lower:
            score += weight
            reasons.append(f"Suspicious phrase in image: '{phrase}' (+{weight} points)")
            break
    
    # Look for inconsistent formatting (sign of copy-paste)
    if has_formatting_inconsistencies(extracted_text):
        score += 20
        reasons.append("Inconsistent text formatting in image (possible copy-paste) (+20 points)")
    
    # Look for multiple currencies (scam indicator)
    currencies_found = len(re.findall(r'USD|EUR|GBP|INR|AUD|CAD', text_lower))
    if currencies_found > 1:
        score += 25
        reasons.append(f"Multiple currencies detected in image ({currencies_found}) (+25 points)")
    
    score = min(score, 95)
    score = max(0, score)
    
    return {
        "risk_score": score,
        "reasons": reasons,
        "is_suspicious": score >= 40
    }


def has_formatting_inconsistencies(text: str) -> bool:
    """
    Check for common formatting inconsistencies that indicate manipulation.
    """
    lines = text.split('\n')
    
    # Check for sudden font size changes (indicated by unusual line lengths)
    line_lengths = [len(line.strip()) for line in lines if line.strip()]
    
    if len(line_lengths) > 3:
        avg_length = sum(line_lengths) / len(line_lengths)
        # If any line is >2x the average length, might be copy-pasted
        for length in line_lengths:
            if length > avg_length * 2:
                return True
    
    return False
