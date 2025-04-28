# API Endpoints for search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging

# Import core components and dependencies
from app.core.logger import get_logger
from app.core.dependencies import get_rag_service # Assuming RAG dependency is in core

# Import service and schema from new locations
from app.services.search_service import SearchService, get_search_service
from app.schemas.search import QueryRequest

# Corrected import path for RAGService
from app.services.rag_service import RAGService

router = APIRouter()
logger = get_logger("api.search")

@router.post("/query/")
async def query(
    request: QueryRequest,
    search_service: SearchService = Depends(get_search_service),
    rag_service: RAGService = Depends(get_rag_service) # Inject RAGService for the service layer
):
    """
    문서에 대한 질의 수행
    """
    logger.info(f"'{request.query[:50]}...' 질의 요청 수신 (API 계층, top_k={request.top_k})")
    if not request.query or not request.query.strip():
        logger.warning("빈 질의 요청")
        raise HTTPException(status_code=400, detail="질의 내용이 비어 있습니다.")

    try:
        result = await search_service.perform_search(rag_service, request.query, request.top_k)
        
        # Check if service layer returned an error
        if isinstance(result, dict) and result.get("error"):
            logger.error(f"서비스 계층 오류: {result['error']}")
            # You might want different status codes based on the error type
            raise HTTPException(status_code=500, detail=f"질의 처리 중 내부 오류 발생: {result['error']}")
            
        return result
        
    except HTTPException as http_exc:
        raise http_exc # Re-raise validation errors etc.
    except Exception as e:
        logger.exception(f"'{request.query[:50]}...' 질의 처리 중 예상치 못한 API 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="질의 처리 중 예상치 못한 서버 오류 발생") 