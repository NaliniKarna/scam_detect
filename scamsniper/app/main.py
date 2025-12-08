from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from app.routers.report import router as report_router
from app.routers import classify, health, email, transaction

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Include routers
app.include_router(classify, prefix="/api")
# app.include_router(report, prefix="/api")
app.include_router(report_router)
app.include_router(email.router)
app.include_router(transaction.router)
app.include_router(health, prefix="/api")
if ocr_available and ocr is not None:
    app.include_router(ocr.router, prefix="/api")

# ------------------------------
# FRONTEND STATIC FILES
# ------------------------------

# Correct frontend directory path
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
frontend_path = os.path.abspath(frontend_path)

if not os.path.exists(frontend_path):
    logger.error(f"Frontend directory does not exist: {frontend_path}")
else:
    logger.info(f"Serving frontend from: {frontend_path}")

# Mount the entire frontend directory at root
# This ensures /style.css, /app.js, /favicon.ico all work
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# Optional: Serve index.html explicitly at root (can be skipped if html=True in mount)
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(frontend_path, "index.html")
    if not os.path.exists(index_file):
        return "<h2>index.html not found in /frontend</h2>"
    return FileResponse(index_file)


# ------------------------------
# OCR Startup Loader
# ------------------------------
@app.on_event("startup")
async def startup_event():
    if ocr_available:
        from app.services.ocr_service import ocr_engine
        logger.info("Loading OCR engine...")
        success = ocr_engine.load()
        if success:
            logger.info("OCR engine loaded successfully")
        else:
            logger.warning("OCR engine failed to load.")