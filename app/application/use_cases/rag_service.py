# Service layer for RAG operations
# ... (other imports) ...

# Import from app locations
from app.core.logger import get_logger
from app.core.config import AppConfig
# Assuming model_manager and document_processor are also in application/use_cases
from app.application.use_cases.model_manager import ModelManager
from app.application.use_cases.document_processor import DocumentProcessor

# ... (rest of the file) ... 