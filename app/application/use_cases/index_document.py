from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from app.domain.entities.document import DocumentEntity
from app.domain.value_objects.document_chunk import DocumentChunk
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.services.document_processing_service import DocumentProcessingService
from app.domain.services.storage_service import StorageService
from app.core.logger import get_logger
from app.core.config import AppConfig

logger = get_logger("application.use_cases.index_document")

@dataclass
class IndexDocumentInput:
    """문서 인덱싱 유스케이스 입력"""
    document_id: str
    chunk_size: int = 1000
    chunk_overlap: int = 200

@dataclass
class IndexDocumentOutput:
    """문서 인덱싱 유스케이스 출력"""
    document_id: str
    chunks_count: int
    success: bool
    error: Optional[str] = None

class IndexDocumentUseCase:
    """문서 인덱싱 유스케이스
    
    저장된 문서를 처리하여 청크로 분할하고 벡터 DB에 인덱싱하는 유스케이스입니다.
    """
    
    def __init__(self,
                 document_repository: DocumentRepository,
                 chunk_repository: ChunkRepository,
                 document_processing_service: DocumentProcessingService,
                 storage_service: StorageService,
                 config: AppConfig):
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.document_processing_service = document_processing_service
        self.storage_service = storage_service
        self.config = config
        logger.info("IndexDocumentUseCase 초기화 완료")
    
    async def execute(self, input_data: IndexDocumentInput) -> IndexDocumentOutput:
        """유스케이스 실행"""
        try:
            # 문서 엔티티 조회
            document = await self.document_repository.find_by_id(input_data.document_id)
            if not document:
                return IndexDocumentOutput(
                    document_id=input_data.document_id,
                    chunks_count=0,
                    success=False,
                    error="DOCUMENT_NOT_FOUND"
                )
            
            # 저장소에서 파일 내용 가져오기
            file_content = await self.storage_service.read_file(input_data.document_id)
            if not file_content:
                return IndexDocumentOutput(
                    document_id=input_data.document_id,
                    chunks_count=0,
                    success=False,
                    error="FILE_NOT_FOUND"
                )
            
            # 문서 청크 생성
            try:
                chunks = self.document_processing_service.create_document_chunks(
                    document_id=document.id,
                    filename=document.filename,
                    file_content=file_content,
                    chunk_size=input_data.chunk_size,
                    chunk_overlap=input_data.chunk_overlap
                )
            except NotImplementedError:
                # 아직 도메인 서비스 구현체가 없는 경우 기존 방식으로 대체
                # 이 부분은 실제 구현에서 제거되어야 함
                logger.warning("문서 처리 서비스 구현체가 없어 임시 처리를 사용합니다. 이 코드는 추후 제거될 예정입니다.")
                chunks = []
                
            # 청크 저장소에 저장
            if chunks:
                await self.chunk_repository.save_chunks(chunks)
                
                # 문서 인덱싱 완료 표시
                document.mark_as_indexed()
                await self.document_repository.update(document)
                
                # 임시 파일 삭제 시도
                try:
                    await self.storage_service.delete_file(input_data.document_id)
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패: {e}")
                
                return IndexDocumentOutput(
                    document_id=input_data.document_id,
                    chunks_count=len(chunks),
                    success=True
                )
            else:
                return IndexDocumentOutput(
                    document_id=input_data.document_id,
                    chunks_count=0,
                    success=False,
                    error="NO_CHUNKS_CREATED"
                )
                
        except Exception as e:
            logger.exception(f"문서 인덱싱 중 오류 발생: {e}")
            return IndexDocumentOutput(
                document_id=input_data.document_id,
                chunks_count=0,
                success=False,
                error=str(e)
            ) 