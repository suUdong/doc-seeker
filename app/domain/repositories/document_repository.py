from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.document import DocumentEntity

class DocumentRepository(ABC):
    """문서 저장소 인터페이스
    
    문서 엔티티의 영속성을 관리하는 추상 인터페이스입니다.
    구체적인 구현은 인프라스트럭처 계층에서 제공됩니다.
    """
    
    @abstractmethod
    async def save(self, document: DocumentEntity) -> str:
        """문서 저장"""
        pass
    
    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[DocumentEntity]:
        """ID로 문서 조회"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[DocumentEntity]:
        """모든 문서 조회"""
        pass
    
    @abstractmethod
    async def update(self, document: DocumentEntity) -> bool:
        """문서 업데이트"""
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """문서 삭제"""
        pass 