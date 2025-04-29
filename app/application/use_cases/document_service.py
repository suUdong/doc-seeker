# Service layer for document related operations
import logging
from app.core.config import AppConfig
# Corrected import paths for services
from app.application.use_cases.rag_service import RAGService 
from app.infrastructure.storage.storage import StorageHandler, get_storage_handler as get_storage_handler_impl
from app.core.logger import get_logger
from app.domain.schemas.document import DocumentResponse # Import schema from the new location
from typing import List, Dict, Any

logger = get_logger("application.document_service")

class DocumentService:

    # Dependencies can be injected here if using a class-based approach
    # or passed as arguments in functions if using a functional approach.
    # Example (functional): def __init__(self, rag_service: RAGService, ...)
    
    async def index_document_background(
        self,
        identifier: str,
        original_filename: str,
        storage_type: str,
        rag_service: RAGService, # Passed from API layer
        config: AppConfig,       # Passed from API layer
    ):
        """문서 인덱싱을 처리하는 백그라운드 작업 (tasks.py 내용 기반)"""
        logger.info(f"'{original_filename}' 문서 인덱싱 시작 (Identifier: {identifier}, Storage: {storage_type}).")
        storage_handler: StorageHandler = get_storage_handler_impl(config) # Get concrete handler

        try:
            file_content = await storage_handler.read_file(identifier)
            if not file_content:
                logger.error(f"저장소에서 파일을 읽지 못했습니다: {identifier}")
                return

            logger.info(f"'{original_filename}' 파일 내용 로드 완료.")
            
            # Assuming index_document takes bytes and filename
            success = await rag_service.index_document(file_content, original_filename)

            if success:
                logger.info(f"'{original_filename}' 문서 인덱싱 성공.")
            else:
                logger.error(f"'{original_filename}' 문서 인덱싱 실패.")

        except FileNotFoundError:
            logger.error(f"인덱싱 처리 중 파일을 찾을 수 없습니다: {identifier}")
        except Exception as e:
            logger.exception(f"'{original_filename}' 문서 인덱싱 중 오류 발생: {e}")
        finally:
            try:
                logger.info(f"처리 후 파일 삭제 시도: {identifier}")
                await storage_handler.delete_file(identifier)
                logger.info(f"파일 삭제 완료: {identifier}")
            except FileNotFoundError:
                logger.warning(f"삭제할 파일을 찾을 수 없습니다: {identifier}")
            except Exception as e:
                logger.exception(f"파일 삭제 중 오류 발생 {identifier}: {e}")

    async def list_documents(self) -> List[DocumentResponse]: # Use the schema from new location
        """
        업로드된 모든 문서 목록 조회 (구현 필요)
        """
        logger.info("문서 목록 조회 로직 수행 (서비스 계층)")
        # TODO: Implement actual document listing logic
        # Example: documents_data = await self.rag_service.list_indexed_documents()
        # return [DocumentResponse(**doc_data) for doc_data in documents_data]
        
        # Returning mock data for now
        mock_documents_data = [
            {
                "id": "mock_id_1",
                "filename": "example1.pdf",
                "upload_date": "2023-10-27T10:00:00Z"
            },
            {
                "id": "mock_id_2",
                "filename": "example2.txt",
                "upload_date": "2023-10-27T11:00:00Z"
            }
        ]
        # Map data to the response schema
        return [DocumentResponse(**doc) for doc in mock_documents_data]

# Dependency function to get service instance (optional, can use Depends(DocumentService))
def get_document_service() -> DocumentService:
    # If DocumentService needs dependencies like RAGService, inject them here
    # Example: return DocumentService(rag_service=Depends(get_rag_service))
    return DocumentService() 