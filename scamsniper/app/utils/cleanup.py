import re

def clean_text(text: str) -> str:
    # very simple cleanup
    return re.sub(r"\s+", " ", text).strip()
