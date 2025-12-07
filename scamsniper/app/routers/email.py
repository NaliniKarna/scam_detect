from fastapi import APIRouter
from pydantic import BaseModel
import re
from app.services.ml_model import ml_classifier
from app.services.url_reputation import url_reputation
from app.services.heuristics import heuristics_engine

router = APIRouter(prefix="/api/email", tags=["Email Fraud Detection"])

class EmailCheck(BaseModel):
    sender: str
    subject: str
    body: str
    attachments: list[str] = []
    # Optional: email authentication headers for DMARC/SPF/DKIM validation
    headers: dict = {}  # Optional headers: {"dmarc": "pass/fail", "spf": "pass/fail", "dkim": "pass/fail"}
    return_path: str | None = None  # Return-Path header
    from_header: str | None = None  # From header (may differ from sender)


def extract_urls(text):
    url_pattern = r"(https?://\S+)"
    return re.findall(url_pattern, text)


def is_suspicious_attachment(file):
    bad_ext = [".html", ".exe", ".zip", ".scr", ".apk"]
    for ext in bad_ext:
        if file.lower().endswith(ext):
            return True
    return False


def check_dmarc_spf_dkim(sender: str, return_path: str | None = None, from_header: str | None = None, headers: dict | None = None):
    """
    Validate DMARC, SPF, and DKIM alignment.
    Checks if sender domain, return-path domain, and from header domain are aligned.
    """
    score = 0
    reasons = []
    
    if headers is None:
        headers = {}
    
    sender_domain = sender.split("@")[-1].lower()
    return_path_domain = return_path.split("@")[-1].lower() if return_path else None
    from_domain = from_header.split("@")[-1].lower() if from_header else None
    
    # Check DMARC status
    dmarc_status = headers.get("dmarc", "unknown").lower()
    if dmarc_status == "fail":
        score += 40
        reasons.append("DMARC validation failed")
    elif dmarc_status == "pass":
        # Reduce suspicion if DMARC passes
        score -= 10  # Small reduction, still check other factors
        reasons.append("DMARC validation passed")
    
    # Check SPF status
    spf_status = headers.get("spf", "unknown").lower()
    if spf_status == "fail":
        score += 35
        reasons.append("SPF validation failed")
    elif spf_status == "pass":
        score -= 5
        reasons.append("SPF validation passed")
    
    # Check DKIM status
    dkim_status = headers.get("dkim", "unknown").lower()
    if dkim_status == "fail":
        score += 35
        reasons.append("DKIM validation failed")
    elif dkim_status == "pass":
        score -= 5
        reasons.append("DKIM validation passed")
    
    # Check domain alignment (sender vs return-path vs from header)
    if return_path_domain and return_path_domain != sender_domain:
        score += 30
        reasons.append("Return-Path domain mismatch (possible spoofing)")
    
    if from_domain and from_domain != sender_domain:
        score += 25
        reasons.append("From header domain mismatch (possible spoofing)")
    
    # Ensure score doesn't go negative
    score = max(0, score)
    
    return score, reasons


def check_sender(sender):
    suspicious_domains = [
        "verify", "secure", "login", "alert", "support", "account"
    ]
    # Common temporary/disposable email domains
    temporary_email_domains = [
        "tempmail", "guerrillamail", "10minutemail", "mailinator", "throwaway",
        "yopmail", "maildrop", "sharklasers", "spam4", "besenica", "temp-mail",
        "trashmail", "fakeinbox", "grr", "guerrillamail", "dispostable", 
        "sharklasers", "fakeinbox", "mailnesia", "temp-mails", "tempmail24",
        "minute-email", "trash-mail", "guerrillamail", "momentary-mail",
        "email-generator", "throw-away-email", "one-time-email"
    ]
    score = 0
    reasons = []

    email_domain = sender.split("@")[-1]

    # Detect temporary/disposable email addresses
    for temp_domain in temporary_email_domains:
        if temp_domain.lower() in email_domain.lower():
            score += 35
            reasons.append("Temporary/disposable email address detected")
            break

    # Free email pretending to be official
    if any(x in sender for x in ["gmail.com", "outlook.com", "yahoo.com"]):
        if any(keyword in sender.lower() for keyword in ["bank", "support", "service"]):
            score += 25
            reasons.append("Free email used for official communication")

    # Check suspicious domain names
    for s in suspicious_domains:
        if s in email_domain.lower():
            score += 20
            reasons.append(f"Domain contains suspicious keyword: {s}")

    return score, reasons


@router.post("/check")
def email_check(payload: EmailCheck):
    risk_score = 0
    reasons = []

    # 0️⃣ Validate DMARC/SPF/DKIM authentication
    dmarc_score, dmarc_reasons = check_dmarc_spf_dkim(
        payload.sender,
        return_path=payload.return_path,
        from_header=payload.from_header,
        headers=payload.headers
    )
    risk_score += dmarc_score
    reasons.extend(dmarc_reasons)

    # 1️⃣ Analyze sender
    sender_score, sender_reasons = check_sender(payload.sender)
    risk_score += sender_score
    reasons.extend(sender_reasons)

    # 2️⃣ Analyze subject using heuristics
    subject_heur = heuristics_engine(payload.subject)
    risk_score += subject_heur["risk"]
    reasons.extend(subject_heur["reasons"])

    # 3️⃣ Analyze body using heuristics + ML
    body_heur = heuristics_engine(payload.body)
    risk_score += body_heur["risk"]
    reasons.extend(body_heur["reasons"])
    
    # Add ML model prediction for body
    ml_pred = ml_classifier.predict(payload.body)
    if ml_pred["label"] == "scam":
        risk_score += int(ml_pred["confidence"] * 30)
        reasons.append(f"AI Model Detection ({round(ml_pred['confidence']*100, 1)}%)")

    # 4️⃣ Extract and evaluate URLs
    urls = extract_urls(payload.body + " " + payload.subject)
    for u in urls:
        url_data = url_reputation(u)
        risk_score += url_data["risk"]
        reasons.extend(url_data["reasons"])

    # 5️⃣ Check attachments
    for file in payload.attachments:
        if is_suspicious_attachment(file):
            risk_score += 30
            reasons.append(f"Suspicious attachment: {file}")

    # Final risk cap (consistent with classify.py)
    risk_score = min(risk_score, 95)

    label = (
        "Safe" if risk_score < 40 else
        "Suspicious" if risk_score < 80 else
        "Scam"
    )

    return {
        "risk_score": risk_score,
        "label": label,
        "reasons": list(set(reasons))  # Remove duplicates
    }
