# Service layer for search operations
import logging
import time
from typing import Any, Dict

# Corrected import paths using app structure
from app.application.use_cases.rag_service import RAGService
from app.core.logger import get_logger
from app.domain.schemas.search import QueryRequest

# ... (rest of the file) ... 