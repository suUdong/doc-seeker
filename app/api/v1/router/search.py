# API Endpoints for search
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.core.logger import get_logger
from app.core.dependencies import (
    get_search_document_use_case,
    get_chat_use_case,
)

from app.api.v1.schemas.search import (
    SearchRequest,
    SearchResponse,
    ChatRequest,
    ChatResponse,
)

from app.application.use_cases.search_document import (
    SearchDocumentUseCase,
    SearchDocumentInput
)

from app.application.use_cases.chat import (
    ChatUseCase,
    ChatInput
)

router = APIRouter()
logger = get_logger("api.search")

@router.post("/documents/", response_model=SearchResponse)
async def search_documents(
    query: SearchRequest,
    search_use_case: SearchDocumentUseCase = Depends(get_search_document_use_case)
):
    """문서에서 쿼리와 관련된 정보를 검색합니다."""
    logger.info(f"검색 요청 수신: {query.query}")
    
    try:
        search_input = SearchDocumentInput(
            query=query.query,
            limit=query.limit or 5,
            filter_conditions=query.filters
        )
        
        result = await search_use_case.execute(search_input)
        
        if not result.success:
            logger.error(f"검색 실패: {result.error}")
            raise HTTPException(status_code=500, detail=f"검색 실패: {result.error}")
        
        return SearchResponse(
            query=query.query,
            results=result.search_results
        )
    
    except Exception as e:
        logger.exception(f"검색 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"검색 처리 중 서버 오류 발생: {e}")

@router.post("/chat/", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    """문서 기반 챗봇: 메시지에 대해 관련 문서를 조회하고 응답을 생성합니다."""
    logger.info(f"챗 요청 수신: {request.message}")
    
    try:
        chat_input = ChatInput(
            message=request.message,
            chat_history=request.history or [],
            limit=request.limit or 5
        )
        
        result = await chat_use_case.execute(chat_input)
        
        if not result.success:
            logger.error(f"챗 응답 생성 실패: {result.error}")
            raise HTTPException(status_code=500, detail=f"챗 응답 생성 실패: {result.error}")
        
        return ChatResponse(
            message=result.message,
            sources=result.sources
        )
    
    except Exception as e:
        logger.exception(f"챗 응답 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"챗 응답 생성 중 서버 오류 발생: {e}") 