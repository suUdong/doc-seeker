# API Endpoints for documents
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from typing import List
import logging

# Import core components and dependencies from new locations
from app.core.config import AppConfig
from app.core.storage import StorageHandler
from app.core.dependencies import get_app_config, get_storage_handler # get_rag_service might be here or elsewhere
from app.core.logger import get_logger

# Import service and schema from new locations
from app.services.document_service import DocumentService, get_document_service
from app.schemas.document import DocumentResponse

# Corrected import path for RAGService
from app.services.rag_service import RAGService
from app.core.dependencies import get_rag_service # Assuming get_rag_service is now in core.dependencies

router = APIRouter()
logger = get_logger("api.documents")

@router.post("/upload/", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    storage_handler: StorageHandler = Depends(get_storage_handler),
    config: AppConfig = Depends(get_app_config),
    rag_service: RAGService = Depends(get_rag_service), # Need rag_service for background task
):
    """문서를 업로드하고 인덱싱을 위한 백그라운드 작업을 시작합니다."""
    logger.info(f"문서 업로드 요청 수신: {file.filename}")

    if file.content_type != "application/pdf":
        logger.warning(f"지원되지 않는 파일 형식: {file.content_type}")
        raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다. PDF 파일을 업로드해주세요.")

    try:
        identifier, original_filename = await storage_handler.save_file(file)
        logger.info(f"파일 저장 완료: Identifier='{identifier}', Original='{original_filename}', Storage='{config.STORAGE_TYPE}'")

        background_tasks.add_task(
            document_service.index_document_background,
            identifier=identifier,
            original_filename=original_filename,
            storage_type=config.STORAGE_TYPE,
            rag_service=rag_service, # Pass dependency explicitly to background task
            config=config,           # Pass dependency explicitly
        )

        return {
            "message": f"'{original_filename}' 파일 업로드 성공. 인덱싱이 백그라운드에서 시작되었습니다.",
            "identifier": identifier,
            "storage_type": config.STORAGE_TYPE
        }

    except Exception as e:
        await file.close() 
        logger.exception(f"파일 업로드 또는 저장 중 오류 발생 ({file.filename}): {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 서버 오류 발생: {e}")
    finally:
        if hasattr(file, 'file') and not file.file.closed:
             await file.close()

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    document_service: DocumentService = Depends(get_document_service)
):
    """
    업로드된 모든 문서 목록 조회
    """
    logger.info("문서 목록 조회 요청 수신 (API 계층)")
    try:
        documents = await document_service.list_documents()
        return documents
    except Exception as e:
        logger.exception(f"문서 목록 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="문서 목록 조회 중 서버 오류 발생") 