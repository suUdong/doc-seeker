from typing import List, Dict, Any, Optional
import logging

from app.domain.services.rag_service import RAGService
from app.infrastructure.llm.llm_service import LLMService
from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger("infrastructure.rag.llama_rag_service")

class LlamaRAGService(RAGService):
    """
    LLaMA 모델을 사용하는 RAG 서비스 구현체
    """
    
    def __init__(self, llm_service: LLMService, config: AppConfig):
        """
        Args:
            llm_service: LLM 서비스 인스턴스
            config: 애플리케이션 설정
        """
        self.llm_service = llm_service
        self.config = config
        logger.info("LlamaRAGService 초기화 완료")
    
    async def generate_answer(
        self, 
        query: str, 
        context: List[str], 
        max_tokens: int = 512, 
        temperature: float = 0.7
    ) -> str:
        """
        주어진 쿼리와 검색된 컨텍스트를 기반으로 응답을 생성합니다.
        
        Args:
            query: 사용자 질의
            context: 관련 문서 컨텍스트 목록
            max_tokens: 생성할 최대 토큰 수 (기본값: 512)
            temperature: 생성 다양성 조절 파라미터 (기본값: 0.7)
            
        Returns:
            생성된 응답 텍스트
        """
        try:
            # 시스템 프롬프트 가져오기
            system_prompt = await self.get_system_prompt()
            
            # 컨텍스트 텍스트 결합
            context_text = "\n\n".join(context) if context else "관련 정보가 없습니다."
            
            # 전체 프롬프트 형성
            full_prompt = f"{system_prompt}\n\n컨텍스트 정보:\n{context_text}\n\n질문: {query}\n\n답변:"
            
            logger.debug(f"생성 프롬프트: {full_prompt[:100]}...")
            
            # LLM을 사용하여 응답 생성
            response = await self.llm_service.generate(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.strip()
            
        except Exception as e:
            logger.exception(f"응답 생성 중 오류 발생: {e}")
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def get_system_prompt(self) -> str:
        """
        시스템 프롬프트를 반환합니다.
        
        Returns:
            시스템 프롬프트 텍스트
        """
        return """당신은 한국어 문서 질의응답 도우미입니다. 
주어진 컨텍스트 정보를 바탕으로 질문에 정확하게 답변해 주세요.
컨텍스트에 관련 정보가 없다면, 알지 못한다고 솔직히 답변하세요.
답변은 간결하고 명확하게 작성하세요."""
    
    async def format_retrieval_context(self, context_items: List[Dict[str, Any]]) -> str:
        """
        검색된 컨텍스트 항목들을 프롬프트에 적합한 형식으로 포맷팅합니다.
        
        Args:
            context_items: 검색된 컨텍스트 항목 목록 (각 항목은 텍스트와 메타데이터 포함)
            
        Returns:
            포맷팅된 컨텍스트 문자열
        """
        if not context_items:
            return "관련 정보가 없습니다."
        
        formatted_contexts = []
        
        for i, item in enumerate(context_items):
            text = item.get("text", "")
            metadata = item.get("metadata", {})
            
            # 메타데이터에서 문서 ID 또는 파일명 가져오기
            doc_id = metadata.get("document_id", "unknown")
            page_num = metadata.get("page_number", "")
            page_info = f", 페이지: {page_num}" if page_num else ""
            
            # 포맷팅된 컨텍스트 항목 생성
            formatted_context = f"[출처 {i+1}] 문서: {doc_id}{page_info}\n{text}\n"
            formatted_contexts.append(formatted_context)
        
        return "\n".join(formatted_contexts) 