from typing import List, Dict, Any, Optional
import uuid
import asyncio
from qdrant_client import QdrantClient 
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.domain.value_objects.document_chunk import DocumentChunk
from app.domain.value_objects.search_query import SearchQuery
from app.domain.repositories.chunk_repository import ChunkRepository
from app.infrastructure.embedding.embedding_service import EmbeddingService
from app.core.logger import get_logger
from app.core.config import AppConfig

logger = get_logger("infrastructure.repository.qdrant_chunk")

class QdrantChunkRepository(ChunkRepository):
    """Qdrant 기반 청크 저장소 구현체
    
    벡터 데이터베이스인 Qdrant를 사용하여 문서 청크를 저장하고 검색합니다.
    검색은 임베딩 기반의 의미적 유사도 검색을 지원합니다.
    """
    
    def __init__(self, 
                 client: QdrantClient, 
                 embedding_service: EmbeddingService,
                 config: AppConfig):
        self.client = client
        self.embedding_service = embedding_service
        self.collection_name = config.QDRANT_COLLECTION_NAME
        self.vector_size = embedding_service.get_vector_size()
        
        # 콜렉션 초기화 보장
        asyncio.create_task(self._ensure_collection())
        logger.info(f"Qdrant 청크 저장소 초기화: 콜렉션={self.collection_name}")
    
    async def _ensure_collection(self):
        """콜렉션이 존재하는지 확인하고, 없으면 생성"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Qdrant 콜렉션 생성: {self.collection_name}")
                
                # 콜렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.vector_size,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                
                # 청크 메타데이터를 위한 페이로드 인덱스 생성
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="source",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD
                )
            else:
                logger.debug(f"Qdrant 콜렉션 이미 존재함: {self.collection_name}")
                
        except Exception as e:
            logger.exception(f"Qdrant 콜렉션 초기화 중 오류: {e}")
    
    async def save_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """청크 저장 (일괄 처리)"""
        if not chunks:
            logger.warning("저장할 청크가 없습니다.")
            return False
        
        try:
            # 텍스트 리스트 추출
            texts = [chunk.text for chunk in chunks]
            
            # 임베딩 생성
            embeddings = await self.embedding_service.embed_texts(texts)
            if not embeddings or len(embeddings) != len(chunks):
                logger.error(f"임베딩 생성 실패: 텍스트 {len(texts)}개, 임베딩 {len(embeddings) if embeddings else 0}개")
                return False
            
            # Qdrant에 저장할 포인트 생성
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                
                # 페이로드 생성 (메타데이터)
                payload = {
                    "text": chunk.text,
                    "source": chunk.source,
                    "document_id": chunk.document_id
                }
                
                # 페이지 번호가 있으면 추가
                if chunk.page is not None:
                    payload["page"] = chunk.page
                
                # 인덱스가 있으면 추가
                if chunk.index is not None:
                    payload["index"] = chunk.index
                
                # 포인트 생성
                points.append(qdrant_models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))
            
            # Qdrant에 포인트 저장
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Qdrant에 {len(points)}개 청크 저장 완료: 문서 ID={chunks[0].document_id}")
            return True
            
        except Exception as e:
            logger.exception(f"청크 저장 중 오류: {e}")
            return False
    
    async def find_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """문서 ID로 청크 검색"""
        try:
            # 문서 ID로 필터링
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=100  # 최대 100개 청크 반환 (필요에 따라 조정)
            )
            
            # 결과가 없으면 빈 리스트 반환
            if not search_result or not search_result.points:
                logger.debug(f"문서 ID에 해당하는 청크 없음: {document_id}")
                return []
            
            # 청크 생성
            chunks = []
            for point in search_result.points:
                payload = point.payload
                
                chunks.append(DocumentChunk(
                    text=payload.get("text", ""),
                    source=payload.get("source", ""),
                    document_id=payload.get("document_id", ""),
                    page=payload.get("page"),
                    index=payload.get("index")
                ))
            
            logger.debug(f"문서 ID로 {len(chunks)}개 청크 조회: {document_id}")
            return chunks
            
        except Exception as e:
            logger.exception(f"문서 ID로 청크 검색 중 오류: {e}")
            return []
    
    async def delete_by_document_id(self, document_id: str) -> bool:
        """문서 ID로 청크 삭제"""
        try:
            # 문서 ID로 포인트 삭제
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            
            logger.info(f"문서 ID로 청크 삭제 완료: {document_id}")
            return True
            
        except Exception as e:
            logger.exception(f"문서 ID로 청크 삭제 중 오류: {e}")
            return False
    
    async def search(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """의미적 유사도 기반 청크 검색"""
        try:
            # 쿼리 텍스트 임베딩
            query_embedding = await self.embedding_service.embed_text(query.text)
            if not query_embedding:
                logger.error("쿼리 임베딩 생성 실패")
                return []
            
            # Qdrant 검색 실행
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=query.top_k
            )
            
            # 결과 변환
            results = []
            for point in search_result:
                payload = point.payload
                
                result = {
                    "text": payload.get("text", ""),
                    "source": payload.get("source", ""),
                    "document_id": payload.get("document_id", ""),
                    "score": point.score
                }
                
                # 페이지 번호가 있으면 추가
                if "page" in payload:
                    result["page"] = payload["page"]
                
                # 인덱스가 있으면 추가
                if "index" in payload:
                    result["index"] = payload["index"]
                
                results.append(result)
            
            logger.debug(f"쿼리 검색 결과: {len(results)}개 청크, 쿼리='{query.text[:50]}...'")
            return results
            
        except Exception as e:
            logger.exception(f"청크 검색 중 오류: {e}")
            return [] 