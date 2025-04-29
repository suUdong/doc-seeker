# API Endpoints for documents
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from typing import List
import logging

# Import core components and dependencies using app path
from app.core.config import AppConfig
from app.infrastructure.storage.storage import StorageHandler
from app.core.dependencies import (
    get_app_config, 
    get_storage_handler,
    get_upload_document_use_case,
    get_index_document_use_case,
    get_document_repository
)
from app.core.logger import get_logger

# Import API schemas
from app.api.v1.schemas.document import DocumentResponse

# Import use cases
from app.application.use_cases.upload_document import UploadDocumentUseCase, UploadDocumentInput
from app.application.use_cases.index_document import IndexDocumentUseCase, IndexDocumentInput
from app.domain.repositories.document_repository import DocumentRepository

router = APIRouter()
logger = get_logger("api.documents")

@router.post("/upload/", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    upload_use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case),
    index_use_case: IndexDocumentUseCase = Depends(get_index_document_use_case)
):
    """문서를 업로드하고 인덱싱을 위한 백그라운드 작업을 시작합니다."""
    logger.info(f"문서 업로드 요청 수신: {file.filename}")

    # 파일 유효성 검사
    if file.content_type != "application/pdf":
        logger.warning(f"지원되지 않는 파일 형식: {file.content_type}")
        raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다. PDF 파일을 업로드해주세요.")

    try:
        # 파일 읽기
        file_content = await file.read()
        
        # 업로드 유스케이스 실행
        upload_input = UploadDocumentInput(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        upload_result = await upload_use_case.execute(upload_input)
        
        # 업로드 실패 시
        if not upload_result.success:
            logger.error(f"파일 업로드 실패: {upload_result.error}")
            raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {upload_result.error}")
        
        # 백그라운드로 인덱싱 작업 실행
        document_id = upload_result.document_id
        background_tasks.add_task(
            index_document_background,
            index_use_case=index_use_case,
            document_id=document_id
        )

        return {
            "message": f"'{file.filename}' 파일 업로드 성공. 인덱싱이 백그라운드에서 시작되었습니다.",
            "identifier": document_id
        }

    except Exception as e:
        if hasattr(file, 'file') and not file.file.closed:
            await file.close()
        logger.exception(f"파일 업로드 또는 저장 중 오류 발생 ({file.filename}): {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 서버 오류 발생: {e}")
    finally:
        if hasattr(file, 'file') and not file.file.closed:
             await file.close()

# 백그라운드 작업용 함수
async def index_document_background(
    index_use_case: IndexDocumentUseCase,
    document_id: str
):
    """인덱싱 작업을 백그라운드에서 실행"""
    logger.info(f"문서 인덱싱 백그라운드 작업 시작: {document_id}")
    
    # 인덱싱 유스케이스 실행
    index_input = IndexDocumentInput(
        document_id=document_id,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    index_result = await index_use_case.execute(index_input)
    
    if index_result.success:
        logger.info(f"문서 인덱싱 완료: {document_id}, 청크 수: {index_result.chunks_count}")
    else:
        logger.error(f"문서 인덱싱 실패: {document_id}, 오류: {index_result.error}")

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    document_repository: DocumentRepository = Depends(get_document_repository)
):
    """
    업로드된 모든 문서 목록 조회
    """
    logger.info("문서 목록 조회 요청 수신 (API 계층)")
    try:
        documents = await document_repository.find_all()
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                content_type=doc.content_type,
                file_size=doc.file_size,
                indexed=doc.indexed,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            ) for doc in documents
        ]
    except Exception as e:
        logger.exception(f"문서 목록 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="문서 목록 조회 중 서버 오류 발생") 