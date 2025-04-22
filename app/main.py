import os
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional

# 중앙화된 로깅 설정 사용
from .logger import get_logger
logger = get_logger('app')

# 임베딩 및 검색 모듈
from .embedding import get_query_embedding, document_embedding_exists
from .retrieval import search_documents

# 응답 생성 모듈
from .generation import generate_response

# 모델 관리자
from .model_manager import model_manager

# API 모델 정의
class QueryRequest(BaseModel):
    query: str = Field(..., description="사용자 질문")
    top_k: int = Field(default=3, description="검색할 최대 문서 수")
    max_tokens: int = Field(default=512, description="생성할 최대 토큰 수")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="생성된 응답")
    sources: List[dict] = Field(..., description="참고한 문서 소스 목록")
    
class HealthResponse(BaseModel):
    status: str = Field(..., description="서비스 상태")
    model_info: dict = Field(..., description="모델 정보")

# FastAPI 애플리케이션 초기화
app = FastAPI(
    title="Document Search & QA API",
    description="문서 검색 및 질의응답 API",
    version="0.1.0"
)

# 헬스체크 엔드포인트
@app.get("/health/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """서비스 상태 확인"""
    # 모델 정보 가져오기
    model_info = model_manager.get_model_info()
    
    return {
        "status": "ok",
        "model_info": model_info
    }

# 질의응답 엔드포인트
@app.post("/api/query/", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    사용자 질문에 대한 응답을 생성합니다.
    """
    try:
        query = request.query
        logger.info(f"질문 접수: {query}")
        
        # 임베딩 존재 여부 확인
        if not document_embedding_exists():
            logger.error("문서 임베딩이 없습니다.")
            raise HTTPException(status_code=500, detail="문서 임베딩이 준비되지 않았습니다.")
        
        # 쿼리 임베딩 생성 및 관련 문서 검색
        query_vector = get_query_embedding(query)
        search_results = search_documents(query_vector, limit=request.top_k)
        
        # 검색 결과가 없는 경우
        if not search_results:
            logger.warning("검색 결과가 없습니다.")
            return {"answer": "죄송합니다. 질문에 관련된 문서를 찾지 못했습니다.", "sources": []}
        
        # 검색된 문서 콘텐츠 추출
        context_chunks = [result["content"] for result in search_results]
        
        # 응답 생성
        answer = generate_response(query, context_chunks, request.max_tokens)
        
        # 검색 결과에서 소스 정보만 추출
        sources = []
        for result in search_results:
            source = {
                "title": result.get("metadata", {}).get("title", "제목 없음"),
                "url": result.get("metadata", {}).get("url", ""),
                "score": result.get("score", 0)
            }
            sources.append(source)
        
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"질의 처리 중 오류가 발생했습니다: {str(e)}")

# 루트 엔드포인트
@app.get("/")
async def root():
    return {"message": "Document Search & QA API"}

# 애플리케이션 시작 시 모델 로드 시도
@app.on_event("startup")
async def startup_event():
    # 모델 로드 시도
    logger.info("애플리케이션 시작: 모델 로드 시도")
    model_manager.load_model()