# Service layer for search operations
import logging
import time
from typing import Any, Dict

# Corrected import path for RAGService
from app.services.rag_service import RAGService
from app.core.logger import get_logger
from app.schemas.search import QueryRequest # Import schema from the new location

logger = get_logger("service.search")

class SearchService:

    async def perform_search(self, rag_service: RAGService, query: str, top_k: int) -> Dict[str, Any]:
        """RAG 서비스를 사용하여 검색을 수행합니다."""
        logger.info(f"'{query[:50]}...' 질의 처리 시작 (서비스 계층, top_k={top_k})")
        start_time = time.time()

        try:
            result = await rag_service.query(query, top_k)
            elapsed_time = time.time() - start_time
            logger.info(f"RAG 서비스 질의 완료: {elapsed_time:.2f}초 소요")
            return result
        except Exception as e:
            logger.exception(f"RAG 서비스 질의 중 오류 발생: {e}")
            # Propagate the error or return a structured error response
            # Returning a dictionary for the API layer to handle
            return {"error": f"검색 처리 중 오류 발생: {e}"}

# Dependency function (optional)
def get_search_service() -> SearchService:
    return SearchService() 