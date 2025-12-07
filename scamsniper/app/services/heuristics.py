import re

def heuristics_engine(text: str):
    risk = 0
    issues = []

    # Scoring rules with weights
    rules = {
        # High-risk phishing indicators
        "Verify Account": (r"verify.*account|confirm.*identity|validate.*account", 25),
        "Urgency Pressure": (r"urgent|immediately|now|right now|asap|24 hours|within.*hours", 20),
        "Account Lockout": (r"locked|blocked|suspended|disabled|closed|frozen", 20),
        "Unauthorized Activity": (r"unauthorized|suspicious activity|compromise|fraud|security alert", 18),
        "Click Link": (r"click here|click link|click below|tap here|open link", 15),
        "Credentials Request": (r"enter.*password|enter.*credentials|login|banking details|card details", 20),
        "Money/Financial": (r"account|funds|money|transfer|payment|card|banking", 10),
        "OTP Request": (r"otp|one time password|verification code|security code", 20),
        "Shortened URL": (r"bit\.ly|tinyurl|t\.co|rb\.gy|short\.link|ow\.ly", 15),
        "Fake Identity": (r"bank|paypal|amazon|apple|microsoft|google security", 15),
        "Time Pressure": (r"expires? in|expires? at|deadline|act now|don't wait|limited time", 18),
        "Threat Language": (r"will be closed|will be locked|will lose|will be charged|will be cancelled", 18),
        "No Contact Info": (r"do not reply|do not respond", 10),
        "Prize/Lottery Scam": (r"won|prize|claim.*reward|lottery|congratulations|you.*selected|you.*chosen", 22),
        "Free Money/Offer": (r"free.*money|claim.*now|earn.*fast|easy money|get rich", 20),
    }

    for reason, (pattern, weight) in rules.items():
        if re.search(pattern, text, re.IGNORECASE):
            risk += weight
            issues.append(reason)

    # Boost score if multiple urgent indicators present
    urgent_count = sum(1 for reason in issues if any(x in reason for x in ["Urgency", "Threat", "Time Pressure", "Account Lockout"]))
    if urgent_count >= 2:
        risk += 30  # Bonus for combining multiple urgency signals

    # Bonus for any 2+ scam indicators
    if len(issues) >= 2:
        risk += 10

    if risk > 100:
        risk = 95

    return {"risk": risk, "reasons": issues}
