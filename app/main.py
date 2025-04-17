from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os

from app.embeddings import embed_text

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="문서 검색 API", description="RAG 시스템을 이용한 문서 검색 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qdrant 클라이언트 설정 - 환경변수 또는 기본값 사용
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_client = QdrantClient(url=QDRANT_URL)

# 컬렉션 이름
COLLECTION_NAME = "documents"

# 컬렉션 초기화 함수
@app.on_event("startup")
async def startup_db_client():
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if COLLECTION_NAME not in collection_names:
            # 컬렉션 생성
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=384,  # all-MiniLM-L6-v2 모델의 임베딩 차원
                    distance=models.Distance.COSINE
                )
            )
            print(f"컬렉션 '{COLLECTION_NAME}'가 생성되었습니다.")
    except Exception as e:
        print(f"시작 오류: {e}")


# 요청/응답 모델 정의
class DocumentIn(BaseModel):
    title: str
    content: str
    source: Optional[str] = None


class QueryIn(BaseModel):
    query: str
    limit: int = 5


class QueryResult(BaseModel):
    content: str
    score: float
    source: Optional[str] = None


@app.post("/documents/", status_code=201)
async def add_document(document: DocumentIn):
    """문서를 추가하고 벡터 데이터베이스에 저장합니다."""
    try:
        # 문서 내용을 임베딩
        embedding = embed_text(document.content)
        
        # Qdrant에 문서 저장
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=qdrant_client.count(collection_name=COLLECTION_NAME).count + 1,
                    vector=embedding,
                    payload={
                        "title": document.title,
                        "content": document.content,
                        "source": document.source
                    }
                )
            ]
        )
        
        return {"message": "문서가 성공적으로 추가되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 추가 중 오류 발생: {str(e)}")


@app.post("/search/", response_model=List[QueryResult])
async def search_documents(query: QueryIn):
    """쿼리와 관련된 문서를 검색합니다."""
    try:
        # 쿼리 임베딩
        query_embedding = embed_text(query.query)
        
        # Qdrant에서 유사한 문서 검색
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=query.limit
        )
        
        # 결과 변환
        results = []
        for result in search_results:
            results.append(QueryResult(
                content=result.payload.get("content"),
                score=result.score,
                source=result.payload.get("source")
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@app.get("/health/")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy"}