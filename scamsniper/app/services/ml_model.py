import numpy as np
import logging

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except Exception:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScamModel:
    def __init__(self, model_name: str = "mrm8488/distilroberta-finetuned-fake-news"):
        # don't load heavy model at import time; allow explicit load
        self.model_name = model_name
        self.tokenizer = None
        self.model = None

    def load(self, local_files_only: bool = False, token: str | None = None):
        """Attempt to load tokenizer and model. Failures are caught and logged.

        Use `local_files_only=True` to avoid network calls.
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("transformers not installed; model unavailable")
            return False

        try:
            kwargs = {}
            if token:
                kwargs["use_auth_token"] = token
            # allow using cached files only when requested
            kwargs["local_files_only"] = local_files_only
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, **kwargs)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, **kwargs)
            logger.info("Loaded model %s", self.model_name)
            return True
        except Exception as e:
            logger.warning("Failed to load model %s: %s", self.model_name, e)
            self.tokenizer = None
            self.model = None
            return False

    def predict(self, text: str):
        # If model isn't loaded, return a safe placeholder prediction
        if self.model is None or self.tokenizer is None:
            return {"label": "unknown", "confidence": 0.0}

        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            outputs = self.model(**inputs)
            logits = outputs.logits.detach().numpy()[0]
            probs = np.exp(logits) / np.sum(np.exp(logits))

            # Map: 0 = real, 1 = fake/scam-like
            label = "safe" if np.argmax(probs) == 0 else "scam"

            return {"label": label, "confidence": float(np.max(probs))}
        except Exception as e:
            logger.warning("Prediction failed: %s", e)
            return {"label": "unknown", "confidence": 0.0}


ml_classifier = ScamModel()
