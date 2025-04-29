from typing import List, Optional, Dict
from datetime import datetime
import copy

from app.domain.entities.document import DocumentEntity
from app.domain.repositories.document_repository import DocumentRepository
from app.core.logger import get_logger

logger = get_logger("infrastructure.repository.memory_document")

class InMemoryDocumentRepository(DocumentRepository):
    """메모리 기반 문서 저장소 구현체
    
    개발 및 테스트 환경에서 사용할 수 있는 간단한 메모리 기반 문서 저장소입니다.
    앱 재시작 시 모든 데이터가 초기화됩니다.
    """
    
    def __init__(self):
        # 문서 ID를 키로, DocumentEntity를 값으로 하는 사전
        self._documents: Dict[str, DocumentEntity] = {}
        logger.info("메모리 기반 문서 저장소 초기화")
    
    async def save(self, document: DocumentEntity) -> str:
        """문서 저장"""
        # 깊은 복사를 통해 원본 객체 수정 방지
        self._documents[document.id] = copy.deepcopy(document)
        logger.debug(f"문서 저장: ID={document.id}, 파일명={document.filename}")
        return document.id
    
    async def find_by_id(self, document_id: str) -> Optional[DocumentEntity]:
        """ID로 문서 조회"""
        document = self._documents.get(document_id)
        if document:
            # 깊은 복사를 통해 원본 객체 수정 방지
            return copy.deepcopy(document)
        logger.debug(f"문서 조회 실패: ID={document_id} (존재하지 않음)")
        return None
    
    async def find_all(self) -> List[DocumentEntity]:
        """모든 문서 조회"""
        logger.debug(f"모든 문서 조회: {len(self._documents)}개 문서 조회됨")
        # 깊은 복사를 통해 원본 객체 수정 방지
        return [copy.deepcopy(doc) for doc in self._documents.values()]
    
    async def update(self, document: DocumentEntity) -> bool:
        """문서 업데이트"""
        if document.id not in self._documents:
            logger.debug(f"문서 업데이트 실패: ID={document.id} (존재하지 않음)")
            return False
        
        # 깊은 복사를 통해 원본 객체 수정 방지
        self._documents[document.id] = copy.deepcopy(document)
        logger.debug(f"문서 업데이트: ID={document.id}, 파일명={document.filename}")
        return True
    
    async def delete(self, document_id: str) -> bool:
        """문서 삭제"""
        if document_id not in self._documents:
            logger.debug(f"문서 삭제 실패: ID={document_id} (존재하지 않음)")
            return False
        
        del self._documents[document_id]
        logger.debug(f"문서 삭제: ID={document_id}")
        return True 