from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Body, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import os
import uuid
from typing import List, Dict, Any, Optional
import time

# 내부 모듈 임포트
from app.model_manager import ModelManager
from app.rag_service import RAGService
from app.document_processor import DocumentProcessor
from app.logger import get_logger

# 로깅 설정
logger = get_logger("api")

# 앱 초기화
app = FastAPI(
    title="DocSeeker API",
    description="문서 기반 질의응답 REST API",
    version="1.0.0"
)

# ModelManager 싱글톤 인스턴스 초기화
model_manager = ModelManager()

# RAG 서비스 초기화
rag_service = RAGService(model_manager=model_manager)

# 기본 모델
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_date: str

@app.get("/health/")
async def health_check():
    """
    서비스 헬스 체크
    """
    return {"status": "ok"}

@app.post("/documents/upload/")
async def upload_document(file: UploadFile = File(...)):
    """
    새 문서 업로드 및 인덱싱
    """
    try:
        # 파일 확장자 확인
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.txt', '.md', '.html']:
            raise HTTPException(
                status_code=400, 
                detail=f"지원되지 않는 파일 형식: {file_extension}. 지원 형식: .pdf, .txt, .md, .html"
            )
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 문서 인덱싱
        logger.info(f"문서 인덱싱 시작: {file.filename}")
        result = rag_service.index_document(file.filename, file_content)
        
        return result
        
    except Exception as e:
        logger.error(f"문서 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/", response_model=List[DocumentResponse])
async def list_documents():
    """
    업로드된 모든 문서 목록 조회
    """
    try:
        # 목업 데이터 반환
        return [
            {
                "id": "1", 
                "filename": "example1.pdf", 
                "upload_date": "2023-09-15"
            },
            {
                "id": "2", 
                "filename": "example2.txt", 
                "upload_date": "2023-09-16"
            }
        ]
    except Exception as e:
        logger.error(f"문서 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/")
async def query(request: QueryRequest):
    """
    문서에 대한 질의 수행
    """
    try:
        if not request.query.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "질의가 비어있습니다."}
            )
        
        logger.info(f"질의 처리 시작: {request.query}")
        start_time = time.time()
        
        # RAG 질의 처리
        result = rag_service.query(request.query, request.top_k)
        
        logger.info(f"질의 처리 완료: {time.time() - start_time:.2f}초 소요")
        return result
        
    except Exception as e:
        logger.error(f"질의 처리 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"질의 처리 중 오류 발생: {str(e)}"}
        )