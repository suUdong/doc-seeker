import os
import uuid
import time
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.logger import get_logger
from app.model_manager import ModelManager
from app.document_processor import DocumentProcessor

logger = get_logger("rag_service")

class RAGService:
    """RAG(Retrieval-Augmented Generation) 서비스 클래스"""
    
    def __init__(self, model_manager: ModelManager = None, collection_name: str = "documents"):
        """
        RAGService 초기화
        
        Args:
            model_manager: ModelManager 인스턴스
            collection_name: Qdrant 컬렉션 이름
        """
        self.model_manager = model_manager or ModelManager()
        self.collection_name = collection_name
        self.vector_size = 768  # 기본 벡터 크기 (모델에 따라 다름)
        
        # Qdrant 클라이언트 초기화
        self.qdrant_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
        self.client = QdrantClient(url=self.qdrant_url)
        
        # 컬렉션 초기화
        self._initialize_collection()
        
        logger.info(f"RAG 서비스 초기화 완료 (Qdrant URL: {self.qdrant_url})")
    
    def _initialize_collection(self):
        """Qdrant 컬렉션 초기화"""
        try:
            # 컬렉션 존재 여부 확인
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"컬렉션 생성됨: {self.collection_name}")
            else:
                logger.info(f"기존 컬렉션 사용: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"컬렉션 초기화 오류: {str(e)}")
            raise
    
    def index_document(self, filename: str, file_content: bytes) -> Dict[str, Any]:
        """
        문서 내용을 인덱싱
        
        Args:
            filename: 파일 이름
            file_content: 파일 내용 (바이트)
            
        Returns:
            Dict: 인덱싱 결과
        """
        try:
            start_time = time.time()
            document_id = str(uuid.uuid4())
            
            # 문서 처리기 초기화
            doc_processor = DocumentProcessor()
            
            # 문서 청크로 분할
            chunks = doc_processor.process(filename, file_content)
            
            if not chunks:
                return {"success": False, "error": "문서에서 텍스트를 추출할 수 없습니다."}
            
            # 각 청크를 임베딩하고 인덱싱
            points = []
            for i, chunk in enumerate(chunks):
                # 임베딩 생성
                embedding = self.model_manager.get_embeddings(chunk["text"])
                
                # Qdrant 포인트 생성
                point = models.PointStruct(
                    id=f"{document_id}_{i}",
                    vector=embedding.tolist(),
                    payload={
                        "document_id": document_id,
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "page": chunk["page"],
                        "chunk_id": i
                    }
                )
                points.append(point)
            
            # 벡터 데이터베이스에 포인트 업로드
            self.client.upload_points(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"문서 인덱싱 완료: {filename} ({len(chunks)} 청크, {time.time() - start_time:.2f}초)")
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks": len(chunks),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"문서 인덱싱 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def query(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        문서에 대한 질의 처리
        
        Args:
            query_text: 질의 텍스트
            top_k: 검색할 최대 문서 수
            
        Returns:
            Dict: 응답 정보
        """
        try:
            if not query_text.strip():
                return {"error": "질의가 비어있습니다."}
            
            # 컨텍스트 검색
            context, sources = self._retrieve_context(query_text, top_k)
            
            if not context:
                return {
                    "answer": "죄송합니다. 질문에 관련된 정보를 찾지 못했습니다.",
                    "sources": []
                }
            
            # 프롬프트 생성
            prompt = f"""다음 정보를 바탕으로 질문에 답변해주세요. 정보에 없는 내용은 답변하지 마세요.

정보:
{context}

질문: {query_text}

답변:"""
            
            # 응답 생성
            answer = self.model_manager.generate_text(prompt, max_length=512)
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"질의 처리 오류: {str(e)}")
            return {"error": str(e)}
    
    def _retrieve_context(self, query: str, top_k: int = 5) -> tuple:
        """
        쿼리와 관련된 컨텍스트 검색
        
        Args:
            query: 검색 쿼리
            top_k: 검색할 최대 문서 수
            
        Returns:
            tuple: (컨텍스트 텍스트, 소스 정보 리스트)
        """
        # 쿼리 임베딩 생성
        query_embedding = self.model_manager.get_embeddings(query)
        
        # 유사 청크 검색
        search_results = self._search_similar_chunks(query_embedding, limit=top_k)
        
        if not search_results:
            return "", []
        
        # 컨텍스트 구성
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results):
            text = result.payload.get("text", "")
            context_parts.append(f"[{i+1}] {text}")
            
            source_info = {
                "source": result.payload.get("source", "알 수 없음"),
                "page": result.payload.get("page", 0),
                "score": result.score
            }
            sources.append(source_info)
        
        context = "\n\n".join(context_parts)
        
        return context, sources
    
    def _search_similar_chunks(self, query_vector, limit=5, score_threshold=0.6):
        """
        쿼리 벡터와 유사한 청크 검색
        
        Args:
            query_vector: 쿼리 임베딩 벡터
            limit: 최대 결과 수
            score_threshold: 최소 유사도 점수
            
        Returns:
            List: 검색 결과
        """
        try:
            # Qdrant 검색 수행
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"청크 검색 오류: {str(e)}")
            return [] 