from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Import from the new core structure
from app.core.config import AppConfig # Assuming AppConfig is still needed, adjust if not
from app.core.logger import get_logger
from app.core import dependencies # Import dependencies module if needed for lifespan

# Import the main API router
from app.api.v1.base import api_router as api_v1_router

logger = get_logger("main") # Use logger from core

# --- Application Lifecycle --- (Remains similar, adjust imports)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    # If config or dependencies are needed during startup, use the core imports
    # config = dependencies.get_app_config()
    # app.state.config = config
    
    # Example: Initialize dependencies if needed
    # dependencies.get_rag_service() # Trigger caching if desired
    # logger.info("Dependencies initialized.")
    
    yield # Application runs here

    logger.info("Application shutdown...")

# --- FastAPI App Initialization ---
def create_app() -> FastAPI:
    logger.info("Creating FastAPI application instance.")
    app = FastAPI(
        title="DocSeeker API",
        description="문서 기반 질의응답 REST API (Refactored Structure)",
        version="1.2.0", # Updated version maybe
        lifespan=lifespan # Include lifespan manager
    )

    # Include the main v1 API router
    logger.info("Including v1 API router...")
    app.include_router(api_v1_router, prefix="/api/v1") # Add prefix for versioning

    # --- Basic Health Check --- (Can remain here or move to a dedicated health endpoint)
    @app.get("/health/", tags=["health"])
    async def health_check():
        """
        서비스 헬스 체크
        """
        logger.debug("Health check requested.")
        return {"status": "ok"}

    logger.info("Application creation complete.")
    return app

app = create_app()

# --- Removed Code Sections ---
# - Dependency functions (moved to dependencies.py)
# - Pydantic models (moved to schemas.py in feature folders)
# - Endpoint definitions (moved to router.py in feature folders)
# - Background task definition (moved to tasks.py)