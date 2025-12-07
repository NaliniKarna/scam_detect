from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import classify, report, health, email, transaction
import logging

logger = logging.getLogger(__name__)

try:
    from app.routers import ocr
    ocr_available = True
except Exception as e:
    logger.warning("OCR router import failed: %s", e)
    ocr_available = False
    ocr = None

app = FastAPI(
    title="ScamSniper",
    version="1.0.0",
    description="AI powered scam detection"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(classify, prefix="/api")
app.include_router(report, prefix="/api")
app.include_router(email.router)
app.include_router(transaction.router)
app.include_router(health, prefix="/api")
if ocr_available and ocr is not None:
    app.include_router(ocr.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Load OCR engine on app startup."""
    if ocr_available:
        from app.services.ocr_service import ocr_engine
        logger.info("Loading OCR engine...")
        success = ocr_engine.load()
        if success:
            logger.info("OCR engine loaded successfully")
        else:
            logger.warning("Failed to load OCR engine; OCR endpoint will return empty results")

@app.get("/")
def root():
    status = {
        "message": "ScamSniper API is running",
        "ocr_available": ocr_available
    }
    return status
