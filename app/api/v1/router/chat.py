from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.core.logger import get_logger
from app.core.dependencies import get_chat_use_case

from app.api.v1.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceDocument
)

from app.application.use_cases.chat import (
    ChatUseCase,
    ChatInput
)

router = APIRouter()
logger = get_logger("api.chat")

@router.post("/", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    """
    문서 기반 챗봇: 메시지에 대해 관련 문서를 조회하고 응답을 생성합니다.
    
    Args:
        request: 채팅 요청 객체
        chat_use_case: 챗 유스케이스
        
    Returns:
        생성된 응답 및 소스 정보
    """
    logger.info(f"챗 요청 수신: {request.message}")
    
    try:
        # 챗 입력 생성
        chat_input = ChatInput(
            message=request.message,
            chat_history=[{"role": m.role, "content": m.content} for m in request.history] if request.history else [],
            limit=request.limit or 5
        )
        
        # 유스케이스 실행
        result = await chat_use_case.execute(chat_input)
        
        if not result.success:
            logger.error(f"챗 응답 생성 실패: {result.error}")
            raise HTTPException(status_code=500, detail=f"챗 응답 생성 실패: {result.error}")
        
        # 소스 문서 생성
        sources = [
            SourceDocument(
                text=source.get("text", ""),
                document_id=source.get("document_id", "unknown"),
                page_number=source.get("page_number", ""),
                score=source.get("score", 0.0)
            ) for source in (result.sources or [])
        ]
        
        return ChatResponse(
            message=result.message,
            sources=sources
        )
    
    except Exception as e:
        logger.exception(f"챗 응답 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"챗 응답 생성 중 서버 오류 발생: {e}") 