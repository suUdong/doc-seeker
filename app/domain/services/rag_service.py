from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class RAGService(ABC):
    """
    RAG(Retrieval-Augmented Generation) 서비스 인터페이스
    
    이 인터페이스는 검색 기반 생성 기능에 필요한 메서드를 정의합니다.
    """
    
    @abstractmethod
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
            max_tokens: 생성할 최대 토큰 수
            temperature: 생성 다양성 조절 파라미터 (높을수록 다양한 답변)
            
        Returns:
            생성된 응답 텍스트
        """
        pass
    
    @abstractmethod
    async def get_system_prompt(self) -> str:
        """
        시스템 프롬프트를 반환합니다.
        
        Returns:
            시스템 프롬프트 텍스트
        """
        pass
    
    @abstractmethod
    async def format_retrieval_context(self, context_items: List[Dict[str, Any]]) -> str:
        """
        검색된 컨텍스트 항목들을 프롬프트에 적합한 형식으로 포맷팅합니다.
        
        Args:
            context_items: 검색된 컨텍스트 항목 목록 (각 항목은 텍스트와 메타데이터 포함)
            
        Returns:
            포맷팅된 컨텍스트 문자열
        """
        pass 