from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from app.domain.value_objects.document_chunk import DocumentChunk
from app.domain.value_objects.search_query import SearchQuery

class ChunkRepository(ABC):
    """문서 청크 저장소 인터페이스
    
    문서 청크의 저장 및 검색 기능을 제공하는 추상 인터페이스입니다.
    벡터 검색 기능도 이 인터페이스를 통해 제공됩니다.
    """
    
    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """청크 저장 (일괄 처리)"""
        pass
    
    @abstractmethod
    async def find_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """문서 ID로 청크 검색"""
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: str) -> bool:
        """문서 ID로 청크 삭제"""
        pass
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """의미적 유사도 기반 청크 검색
        
        Returns:
            List[Dict[str, Any]]: 검색 결과 (점수, 청크 등 포함)
        """
        pass 