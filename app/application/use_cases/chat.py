from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from app.domain.services.rag_service import RAGService
from app.domain.repositories.chunk_repository import ChunkRepository
from app.core.logger import get_logger
from app.core.config import AppConfig

logger = get_logger("application.use_cases.chat")

@dataclass
class ChatInput:
    """챗 요청 입력 데이터"""
    message: str
    chat_history: List[Dict[str, str]] = None
    limit: int = 5

@dataclass
class ChatOutput:
    """챗 요청 출력 데이터"""
    success: bool
    message: str
    sources: List[Dict[str, Any]] = None
    error: Optional[str] = None

class ChatUseCase:
    """
    문서 기반 챗봇 유스케이스
    
    사용자 메시지에 대해 관련 문서를 검색하고 RAG 기반 응답을 생성합니다.
    """
    
    def __init__(
        self,
        chunk_repository: ChunkRepository,
        rag_service: RAGService,
        config: AppConfig
    ):
        """
        Args:
            chunk_repository: 청크 저장소
            rag_service: RAG 서비스
            config: 애플리케이션 설정
        """
        self.chunk_repository = chunk_repository
        self.rag_service = rag_service
        self.config = config
        logger.info("ChatUseCase 초기화 완료")
    
    async def execute(self, input_data: ChatInput) -> ChatOutput:
        """
        유스케이스 실행: 사용자 메시지에 대한 문서 기반 응답 생성
        
        Args:
            input_data: 챗 입력 데이터
            
        Returns:
            ChatOutput: 응답 메시지 및 소스 정보
        """
        try:
            logger.info(f"챗 유스케이스 실행: 메시지={input_data.message[:30]}...")
            
            # 검색 제한 수 확인
            limit = input_data.limit or 5
            
            # 관련 문서 검색
            search_results = await self.chunk_repository.search(
                query=input_data.message,
                limit=limit
            )
            
            if not search_results:
                logger.warning("관련 문서를 찾을 수 없습니다.")
                return ChatOutput(
                    success=True,
                    message="질문에 관련된 정보를 찾을 수 없습니다. 다른 질문을 해보세요.",
                    sources=[]
                )
            
            # 검색 결과에서 텍스트 추출
            contexts = []
            sources = []
            
            for item in search_results:
                text = item.text
                metadata = item.metadata.dict() if hasattr(item.metadata, 'dict') else item.metadata
                
                contexts.append(text)
                sources.append({
                    "text": text,
                    "document_id": metadata.get("document_id", "unknown"),
                    "page_number": metadata.get("page_number", ""),
                    "score": item.score if hasattr(item, 'score') else 0.0
                })
            
            # RAG 서비스를 사용하여 응답 생성
            answer = await self.rag_service.generate_answer(
                query=input_data.message,
                context=contexts,
                max_tokens=512,  # 설정에서 가져올 수도 있음
                temperature=0.7   # 설정에서 가져올 수도 있음
            )
            
            logger.info(f"챗 응답 생성 완료: {answer[:30]}...")
            
            return ChatOutput(
                success=True,
                message=answer,
                sources=sources
            )
            
        except Exception as e:
            logger.exception(f"챗 유스케이스 실행 중 오류 발생: {e}")
            return ChatOutput(
                success=False,
                message="오류가 발생했습니다. 나중에 다시 시도해주세요.",
                error=str(e)
            ) 