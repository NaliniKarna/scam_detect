import re
from urllib.parse import urlparse

def url_reputation(url: str):
    """Analyze URL for scam indicators without relying on external APIs."""
    if not url:
        return {"risk": 0, "reasons": []}
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    full_url = url.lower()
    
    reasons = []
    risk = 0

    # Suspicious domain patterns (phishing tactics)
    suspicious_patterns = {
        "KYC/Bank Update": (r"kyc|verify.*account|update.*bank|confirm.*identity", 35),
        "Fake Login": (r"login|signin|sign-in|authentication|verify.*password", 30),
        "Fake Bank": (r"bank.*verify|secure.*bank|mybank|bankupdate", 35),
        "Fake PayPal": (r"paypal|ebay.*verify", 30),
        "Fake Amazon": (r"amazon.*verify|amazone", 30),
        "Fake Apple": (r"apple.*verify|icloud.*verify|icloud.*login", 30),
        "Credential Harvesting": (r"secure|verify|confirm|authenticate|login", 20),
        "Prize/Giveaway Scam": (r"giveaway|claim.*reward|claim.*now|prize|won.*prize|free.*prize", 35),
        "Urgent Action": (r"urgent|immediate|act.*now|claim.*now|hurry", 25),
    }

    for pattern_name, (pattern, weight) in suspicious_patterns.items():
        if re.search(pattern, domain + full_url):
            risk += weight
            reasons.append(pattern_name)

    # Suspicious TLDs (uncommon extensions often used for scams)
    suspicious_tlds = {
        ".xyz": 20,
        ".click": 20,
        ".online": 20,
        ".site": 15,
        ".top": 15,
        ".win": 20,  # Commonly used for giveaway/lottery scams
        ".bid": 20,
        ".party": 15,
        ".download": 18,
        ".review": 18,
        ".tk": 25,  # Free TLD, commonly abused
        ".ml": 25,  # Free TLD, commonly abused
        ".ga": 25,  # Free TLD, commonly abused
    }

    for tld, tld_risk in suspicious_tlds.items():
        if domain.endswith(tld):
            risk += tld_risk
            reasons.append(f"Suspicious TLD: {tld}")
            break

    # Check for IP address instead of domain (suspicious)
    if re.match(r"^\d+\.\d+\.\d+\.\d+", domain):
        risk += 30
        reasons.append("IP address used instead of domain")

    # Check for homograph attacks (lookalike domains)
    homograph_patterns = {
        "Paypa1": r"paypa[1l]",  # paypa1 or paypал
        "Goog1e": r"goog[1l]e",
        "Afrnazon": r"amaz[0o]n",
    }

    for pattern_name, pattern in homograph_patterns.items():
        if re.search(pattern, domain):
            risk += 25
            reasons.append(f"Homograph attack: {pattern_name}")

    # Cap risk at 100
    if risk > 100:
        risk = 95

    return {"risk": risk, "reasons": reasons}
