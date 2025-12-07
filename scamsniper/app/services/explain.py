def explain(pred, heuristics, url_data):
    reasons = []

    if pred["label"] == "scam":
        reasons.append(f"AI Model High Confidence ({round(pred['confidence']*100,2)}%)")

    reasons.extend(heuristics["reasons"])

    if url_data:
        reasons.extend(url_data["reasons"])

    return reasons
