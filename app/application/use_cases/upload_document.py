from dataclasses import dataclass
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from app.domain.entities.document import DocumentEntity
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.services.storage_service import StorageService
from app.core.logger import get_logger

logger = get_logger("application.use_cases.upload_document")

@dataclass
class UploadDocumentInput:
    """문서 업로드 유스케이스 입력"""
    file_content: bytes
    filename: str
    content_type: str
    
@dataclass
class UploadDocumentOutput:
    """문서 업로드 유스케이스 출력"""
    document_id: str
    message: str
    success: bool
    error: Optional[str] = None

class UploadDocumentUseCase:
    """문서 업로드 유스케이스
    
    문서 파일을 받아 저장하고 DocumentEntity를 생성하는 유스케이스입니다.
    """
    
    def __init__(self, 
                 document_repository: DocumentRepository,
                 storage_service: StorageService):
        self.document_repository = document_repository
        self.storage_service = storage_service
        logger.info("UploadDocumentUseCase 초기화 완료")
        
    async def execute(self, input_data: UploadDocumentInput) -> UploadDocumentOutput:
        """유스케이스 실행"""
        try:
            # 파일 유효성 검사
            if not self._validate_file(input_data.filename, input_data.content_type):
                return UploadDocumentOutput(
                    document_id="",
                    message="지원되지 않는 파일 형식입니다.",
                    success=False,
                    error="UNSUPPORTED_FILE_TYPE"
                )
            
            # 스토리지에 파일 저장
            # storage_service는 기존 인프라 구현체를 재사용
            identifier, original_filename = await self.storage_service.save_file({
                "filename": input_data.filename,
                "content": input_data.file_content
            })
            
            # 문서 엔티티 생성
            document = DocumentEntity(
                id=identifier,
                filename=original_filename,
                upload_date=datetime.now(),
                metadata={"content_type": input_data.content_type, "size": len(input_data.file_content)},
                indexed=False
            )
            
            # 문서 저장소에 저장
            await self.document_repository.save(document)
            
            return UploadDocumentOutput(
                document_id=identifier,
                message=f"'{original_filename}' 파일 업로드 성공",
                success=True
            )
            
        except Exception as e:
            logger.exception(f"문서 업로드 중 오류 발생: {e}")
            return UploadDocumentOutput(
                document_id="",
                message="문서 업로드 중 오류가 발생했습니다.",
                success=False,
                error=str(e)
            )
    
    def _validate_file(self, filename: str, content_type: str) -> bool:
        """파일 유효성 검사"""
        # 지원되는 파일 형식 확인
        supported_types = ["application/pdf", "text/plain"]
        return content_type in supported_types 