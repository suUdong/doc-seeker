# Router for document-related endpoints
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from typing import List
import logging

from app.config import AppConfig
from app.rag.rag_service import RAGService
from app.core.storage import StorageHandler
from app.documents.schemas import DocumentResponse
from app.documents.tasks import process_document_indexing
# Import dependency functions
from app.dependencies import get_rag_service, get_storage_handler, get_app_config
from app.logger import get_logger

router = APIRouter(
    prefix="/documents", # Prefix for all routes in this router
    tags=["documents"] # Tag for OpenAPI documentation
)

logger = get_logger("router.documents")

@router.post("/upload/", status_code=202) # Updated path to be relative to prefix
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rag_service: RAGService = Depends(get_rag_service),
    storage_handler: StorageHandler = Depends(get_storage_handler),
    config: AppConfig = Depends(get_app_config),
):
    """문서를 업로드하고 인덱싱을 위한 백그라운드 작업을 시작합니다."""
    logger.info(f"문서 업로드 요청 수신: {file.filename}")

    # Validate file type if necessary (example for PDF)
    # You might want to move validation logic to a dedicated function or service
    if file.content_type != "application/pdf":
        logger.warning(f"지원되지 않는 파일 형식: {file.content_type}")
        raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다. PDF 파일을 업로드해주세요.")

    try:
        # Save file using the storage handler
        identifier, original_filename = await storage_handler.save_file(file)
        logger.info(f"파일 저장 완료: Identifier='{identifier}', Original='{original_filename}', Storage='{config.STORAGE_TYPE}'")

        # Add indexing task to background
        background_tasks.add_task(
            process_document_indexing,
            identifier,
            original_filename,
            config.STORAGE_TYPE, # Pass storage type
            rag_service, # Pass the RAG service instance
            config,      # Pass the config instance
        )

        return {
            "message": f"'{original_filename}' 파일 업로드 성공. 인덱싱이 백그라운드에서 시작되었습니다.",
            "identifier": identifier,
            "storage_type": config.STORAGE_TYPE
        }

    except Exception as e:
        # Ensure file is closed if save_file fails before reading it
        # (StorageHandler implementation should ideally handle this)
        await file.close() # Make sure to close the file stream on error
        logger.exception(f"파일 업로드 또는 저장 중 오류 발생 ({file.filename}): {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 서버 오류 발생: {e}")
    finally:
        # Ensure file is closed after successful save or if an error occurs later
        if not file.file.closed: # Check if file is not already closed
             await file.close()

@router.get("/", response_model=List[DocumentResponse]) # Updated path
async def list_documents(
    # rag_service: RAGService = Depends(get_rag_service) # Uncomment if needed
):
    """
    업로드된 모든 문서 목록 조회 (현재 목업 데이터)
    """
    logger.info("문서 목록 조회 요청 수신")
    try:
        # TODO: Implement actual document listing logic using RAGService or another mechanism
        # Example: documents = await rag_service.list_indexed_documents()
        # For now, returning mock data
        mock_documents = [
            {
                "id": "mock_id_1",
                "filename": "example1.pdf",
                "upload_date": "2023-10-27T10:00:00Z" # Use ISO format for consistency
            },
            {
                "id": "mock_id_2",
                "filename": "example2.txt",
                "upload_date": "2023-10-27T11:00:00Z"
            }
        ]
        return mock_documents
    except Exception as e:
        logger.exception(f"문서 목록 조회 중 오류 발생: {e}")
        # Use logger.exception to include traceback
        raise HTTPException(status_code=500, detail="문서 목록 조회 중 서버 오류 발생") 