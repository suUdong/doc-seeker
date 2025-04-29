from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from app.domain.value_objects.search_query import SearchQuery
from app.domain.repositories.chunk_repository import ChunkRepository
from app.core.logger import get_logger

logger = get_logger("application.use_cases.search_documents")

@dataclass
class SearchDocumentsInput:
    """문서 검색 유스케이스 입력"""
    query_text: str
    top_k: int = 5

@dataclass
class SearchResult:
    """검색 결과 항목"""
    text: str
    source: str
    score: float
    page: Optional[int] = None
    document_id: Optional[str] = None

@dataclass
class SearchDocumentsOutput:
    """문서 검색 유스케이스 출력"""
    results: List[SearchResult]
    query: str
    success: bool
    error: Optional[str] = None

class SearchDocumentsUseCase:
    """문서 검색 유스케이스
    
    사용자 쿼리를 기반으로 관련 문서 청크를 검색하는 유스케이스입니다.
    """
    
    def __init__(self, chunk_repository: ChunkRepository):
        self.chunk_repository = chunk_repository
    
    async def execute(self, input_data: SearchDocumentsInput) -> SearchDocumentsOutput:
        """유스케이스 실행"""
        try:
            # 입력 유효성 검사
            if not input_data.query_text or input_data.query_text.isspace():
                return SearchDocumentsOutput(
                    results=[],
                    query=input_data.query_text,
                    success=False,
                    error="EMPTY_QUERY"
                )
            
            if input_data.top_k < 1:
                input_data.top_k = 5  # 기본값 설정
            
            # 도메인 값 객체 생성
            try:
                query = SearchQuery(
                    text=input_data.query_text,
                    top_k=input_data.top_k
                )
            except ValueError as e:
                return SearchDocumentsOutput(
                    results=[],
                    query=input_data.query_text,
                    success=False,
                    error=str(e)
                )
            
            # 청크 저장소 검색 실행
            search_results = await self.chunk_repository.search(query)
            
            # 결과 변환
            results = []
            for result in search_results:
                results.append(SearchResult(
                    text=result.get("text", ""),
                    source=result.get("source", ""),
                    score=result.get("score", 0.0),
                    page=result.get("page"),
                    document_id=result.get("document_id")
                ))
            
            return SearchDocumentsOutput(
                results=results,
                query=input_data.query_text,
                success=True
            )
            
        except Exception as e:
            logger.exception(f"문서 검색 중 오류 발생: {e}")
            return SearchDocumentsOutput(
                results=[],
                query=input_data.query_text,
                success=False,
                error=str(e)
            ) 