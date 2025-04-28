# Service layer for RAG operations
import os
import uuid
import time
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Import from new locations
from app.core.logger import get_logger
from app.core.config import AppConfig
# Corrected paths assuming these are now in app/services/
from app.services.model_manager import ModelManager 
from app.services.document_processor import DocumentProcessor 

logger = get_logger("service.rag")

class RAGService:
    """RAG(Retrieval-Augmented Generation) 서비스 클래스"""
    
    def __init__(self, config: AppConfig, model_manager: ModelManager, collection_name: Optional[str] = None):
        """
        RAGService 초기화
        
        Args:
            config: 설정 객체 (AppConfig)
            model_manager: ModelManager 인스턴스 (Injected)
            collection_name: Qdrant 컬렉션 이름 (None이면 config 사용)
        """
        self.config = config
        self.model_manager = model_manager # Use injected model manager
        self.collection_name = collection_name or config.QDRANT_COLLECTION_NAME
        # TODO: Get vector_size from the model_manager or config based on the embedding model
        self.vector_size = 768  # Placeholder - should be dynamic
        
        # Qdrant 클라이언트 초기화 (Consider moving Qdrant client setup to a dependency)
        self.qdrant_url = config.QDRANT_HOST # Use QDRANT_HOST from config
        qdrant_port = config.QDRANT_PORT
        # If Qdrant needs API key or runs on HTTPS, adjust connection accordingly
        self.client = QdrantClient(host=self.qdrant_url, port=qdrant_port)
        
        # 컬렉션 초기화
        self._initialize_collection()
        
        logger.info(f"RAG 서비스 초기화 완료 (Qdrant Host: {self.qdrant_url}:{qdrant_port}, Collection: {self.collection_name})")
    
    def _initialize_collection(self):
        """Qdrant 컬렉션 초기화"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
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
    
    async def index_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        문서 내용을 인덱싱 (기존 RAGService.index_document 로직 기반)
        
        Args:
            file_content: 파일 내용 (바이트)
            filename: 파일 이름
            
        Returns:
            Dict: 인덱싱 결과
        """
        try:
            start_time = time.time()
            document_id = str(uuid.uuid4())
            
            # TODO: DocumentProcessor should ideally be injected
            # For now, instantiate it here (assuming it doesn't need config in init)
            # Or, modify RAGService __init__ to accept DocumentProcessor dependency
            doc_processor = DocumentProcessor()
            # Pass config values directly if needed by process method
            # chunk_size = self.config.DOCUMENT_CHUNK_SIZE 
            # chunk_overlap = self.config.DOCUMENT_CHUNK_OVERLAP
            chunk_size = 1000 # Example value, get from config
            chunk_overlap = 200 # Example value, get from config
            chunks = doc_processor.process(filename, file_content, chunk_size, chunk_overlap)
            
            if not chunks:
                logger.warning(f"문서에서 텍스트를 추출할 수 없습니다: {filename}")
                return {"success": False, "error": "문서에서 텍스트를 추출할 수 없습니다."}
            
            points = []
            for i, chunk in enumerate(chunks):
                try:
                    # Use injected model_manager for embeddings
                    embedding = await self.model_manager.get_embeddings(chunk["text"])
                    if embedding is None:
                        logger.warning(f"청크 임베딩 실패: {filename}, chunk {i}")
                        continue

                    point_id = str(uuid.uuid4())
                    point = models.PointStruct(
                        id=point_id,
                        vector=embedding.tolist(), # Assuming embedding is numpy array
                        payload={
                            "document_id": document_id,
                            "text": chunk["text"],
                            "source": chunk["source"],
                            "page": chunk.get("page"),
                            "chunk_id": i
                        }
                    )
                    points.append(point)
                except Exception as emb_err:
                    logger.error(f"청크 처리 중 오류 발생: {filename}, chunk {i} - {str(emb_err)}")
                    continue 

            if not points:
                logger.error(f"유효한 청크가 없어 인덱싱할 수 없습니다: {filename}")
                return {"success": False, "error": "문서 처리 중 유효한 내용을 찾지 못했습니다."}

            # TODO: Make batch size configurable via self.config
            batch_size = 100 # Example batch size
            uploaded_count = 0
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                try:
                    # Note: upload_points might be synchronous depending on the client version
                    self.client.upload_points(
                        collection_name=self.collection_name,
                        points=batch,
                        wait=True
                    )
                    uploaded_count += len(batch)
                except Exception as upload_err:
                    logger.error(f"Qdrant 포인트 업로드 오류: {filename} - {str(upload_err)}")
                    return {"success": False, "error": f"데이터베이스 업로드 중 오류 발생: {str(upload_err)}"}

            logger.info(f"Qdrant에 {uploaded_count}개 포인트 업로드 완료.")
            logger.info(f"문서 인덱싱 완료: {filename} ({time.time() - start_time:.2f}초)")
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_processed": len(chunks),
                "points_indexed": uploaded_count,
                "filename": filename
            }
            
        except Exception as e:
            logger.exception(f"문서 인덱싱 오류 ({filename}): {e}")
            return {"success": False, "error": f"문서 인덱싱 중 예상치 못한 오류 발생: {str(e)}"}
    
    async def query(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        문서에 대한 질의 처리 (기존 RAGService.query 로직 기반)
        
        Args:
            query_text: 질의 텍스트
            top_k: 검색할 최대 문서 수
            
        Returns:
            Dict: 응답 정보
        """
        try:
            if not query_text.strip():
                logger.warning("빈 질의가 입력되었습니다.")
                return {"error": "질의가 비어있습니다."}
            
            context, sources = await self._retrieve_context(query_text, top_k)
            
            if not context:
                logger.info(f"관련 정보 없음: '{query_text[:50]}...'")
                return {"answer": "죄송합니다. 질문에 관련된 정보를 찾지 못했습니다.", "sources": []}
            
            # TODO: Get prompt template from config
            # prompt_template = self.config.QA_PROMPT_TEMPLATE
            prompt_template = "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            prompt = prompt_template.format(context=context, query=query_text)
            
            # Use injected model_manager for generation
            # TODO: Get max_length from config
            # max_length = self.config.MAX_ANSWER_LENGTH
            max_length = 512 # Example max length
            answer = await self.model_manager.generate_text(prompt, max_length=max_length)
            
            logger.info(f"질의 처리 완료: '{query_text[:50]}...'")
            return {"answer": answer.strip(), "sources": sources}
            
        except Exception as e:
            logger.exception(f"질의 처리 오류: {e}")
            return {"error": f"질의 처리 중 예상치 못한 오류 발생: {str(e)}"}
    
    async def _retrieve_context(self, query: str, top_k: int = 5) -> tuple:
        """
        쿼리와 관련된 컨텍스트 검색
        """
        try:
            query_embedding = await self.model_manager.get_embeddings(query)
            if query_embedding is None:
                logger.error(f"쿼리 임베딩 생성 실패: '{query[:50]}...'")
                return "", []
            
            # TODO: Get score_threshold from config
            # score_threshold = self.config.QDRANT_SCORE_THRESHOLD
            score_threshold = 0.7 # Example threshold
            search_results = self._search_similar_chunks(
                query_embedding.tolist(),
                limit=top_k,
                score_threshold=score_threshold
            )
            
            if not search_results:
                logger.info(f"유사 청크 검색 결과 없음: '{query[:50]}...'")
                return "", []
            
            context_parts = []
            sources = []
            seen_sources = set()
            
            for hit in search_results:
                payload = hit.payload
                if payload and "text" in payload and "source" in payload:
                    context_parts.append(payload["text"])
                    source_key = (payload["source"], payload.get("page"))
                    if source_key not in seen_sources:
                        sources.append({
                            "source": payload["source"],
                            "page": payload.get("page"),
                            "score": hit.score
                        })
                        seen_sources.add(source_key)
                        
            context = "\n\n".join(context_parts)
            logger.info(f"컨텍스트 검색 완료 ({len(sources)} sources): '{query[:50]}...'")
            return context, sources
            
        except Exception as e:
            logger.exception(f"컨텍스트 검색 중 오류: {e}")
            return "", []

    def _search_similar_chunks(self, query_vector: List[float], limit: int = 5, score_threshold: Optional[float] = None) -> List[models.ScoredPoint]:
        """
        벡터 데이터베이스에서 유사한 청크 검색
        """
        try:
            search_request = models.SearchRequest(
                vector=query_vector,
                limit=limit,
                with_payload=True,
                score_threshold=score_threshold
            )
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=None, # Add filters if needed
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            logger.debug(f"유사 청크 검색 결과 수: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"유사 청크 검색 오류: {str(e)}")
            return []

# Note: The get_rag_service dependency function in core/dependencies.py 
# should be updated to initialize and return this RAGService class, injecting ModelManager and AppConfig. 