# FastAPI dependency functions 
from functools import lru_cache
from fastapi import Depends
import logging

# Core components
from app.core.config import AppConfig
from app.core.storage import StorageHandler, get_storage_handler as get_storage_handler_from_core
from app.core.logger import get_logger

# Services from the new location
from app.services.model_manager import ModelManager
from app.services.rag_service import RAGService
# DocumentProcessor might also become a dependency if needed
# from app.services.document_processor import DocumentProcessor, get_document_processor

logger = get_logger("core.dependencies")

# --- Dependency Functions ---

# Configuration Loader (Consider simplifying if AppConfig directly reads env vars)
# Keep load_config if it does more complex loading/validation
# from app.core.config import load_config 
@lru_cache()
def get_app_config() -> AppConfig:
    """Provides the application configuration object."""
    logger.info("Loading/Providing application configuration.")
    # Assuming AppConfig() reads env vars or uses a settings management library
    # If load_config is used, call it here: return load_config()
    try:
        return AppConfig()
    except Exception as e:
        logger.exception("Failed to load application configuration!")
        raise RuntimeError("Could not load application configuration") from e

@lru_cache()
def get_model_manager(config: AppConfig = Depends(get_app_config)) -> ModelManager:
    """Provides a singleton ModelManager instance, injecting config."""
    logger.info("Initializing/Providing ModelManager instance.")
    try:
        return ModelManager(config=config)
    except Exception as e:
        logger.exception("Failed to initialize ModelManager!")
        raise RuntimeError("Could not initialize ModelManager") from e

@lru_cache()
def get_rag_service(
    config: AppConfig = Depends(get_app_config),
    model_manager: ModelManager = Depends(get_model_manager)
) -> RAGService:
    """Provides a singleton RAGService instance, injecting config and model_manager."""
    logger.info("Initializing/Providing RAGService instance.")
    try:
        # Pass the required dependencies (config, model_manager) during initialization
        return RAGService(config=config, model_manager=model_manager)
    except Exception as e:
        logger.exception("Failed to initialize RAGService!")
        raise RuntimeError("Could not initialize RAGService") from e

def get_storage_handler(
    config: AppConfig = Depends(get_app_config)
) -> StorageHandler:
    """Provides a StorageHandler instance based on the configuration."""
    logger.debug(f"Providing StorageHandler instance for type: {config.STORAGE_TYPE}")
    # Assuming get_storage_handler_from_core is the actual factory function
    return get_storage_handler_from_core(config)

# Add other dependencies like DocumentProcessor if needed
# @lru_cache()
# def get_document_processor(config: AppConfig = Depends(get_app_config)) -> DocumentProcessor:
#    logger.info("Initializing/Providing DocumentProcessor instance.")
#    return DocumentProcessor(config=config) # Or without config if not needed in init 