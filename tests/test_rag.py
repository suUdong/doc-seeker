import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from app.rag_service import RAGService
from app.document_processor import DocumentProcessor

class TestRAG:
    """RAG 관련 테스트"""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Qdrant 클라이언트 모킹"""
        mock_client = MagicMock()
        
        # search 메서드 모킹
        search_result = [
            MagicMock(payload={"text": "테스트 문서 내용 1", "source": "test1.pdf", "page": 1}, score=0.95),
            MagicMock(payload={"text": "테스트 문서 내용 2", "source": "test1.pdf", "page": 2}, score=0.85),
            MagicMock(payload={"text": "무관한 내용", "source": "test2.pdf", "page": 1}, score=0.55)
        ]
        mock_client.search.return_value = search_result
        
        return mock_client
    
    @pytest.fixture
    def mock_model_manager(self):
        """ModelManager 모킹"""
        mock_manager = MagicMock()
        
        # get_embeddings 메서드 모킹
        mock_manager.get_embeddings.return_value = np.random.rand(768)
        
        # generate_text 메서드 모킹
        mock_manager.generate_text.return_value = "이것은 테스트 응답입니다."
        
        return mock_manager
    
    @pytest.fixture
    def rag_service(self, mock_qdrant_client, mock_model_manager):
        """테스트용 RAG 서비스"""
        with patch('app.rag_service.QdrantClient', return_value=mock_qdrant_client):
            return RAGService(model_manager=mock_model_manager)
    
    def test_document_indexing(self, rag_service, mock_qdrant_client):
        """문서 인덱싱 테스트"""
        # 문서 처리기 모킹
        mock_doc_processor = MagicMock()
        mock_doc_processor.process.return_value = [
            {"text": "청크 1", "source": "test.pdf", "page": 1},
            {"text": "청크 2", "source": "test.pdf", "page": 1}
        ]
        
        with patch('app.rag_service.DocumentProcessor', return_value=mock_doc_processor):
            # ASCII 문자열만 사용하는 바이트 데이터
            file_content = b"Test file content"
            result = rag_service.index_document("test.pdf", file_content)
            
            # 문서 처리기가 호출되었는지 확인
            mock_doc_processor.process.assert_called_once()
            
            # Qdrant에 points_batch 함수가 호출되었는지 확인
            mock_qdrant_client.upload_points.assert_called_once()
            
            # 성공적인 결과 반환 확인
            assert result["success"] is True
            assert "document_id" in result
    
    def test_query_processing(self, rag_service, mock_model_manager, mock_qdrant_client):
        """질의 처리 테스트"""
        query = "테스트 질문입니다"
        response = rag_service.query(query)
        
        # 임베딩이 생성되었는지 확인
        mock_model_manager.get_embeddings.assert_called_with(query)
        
        # Qdrant 검색이 호출되었는지 확인
        mock_qdrant_client.search.assert_called_once()
        
        # 모델 응답 생성이 호출되었는지 확인
        mock_model_manager.generate_text.assert_called_once()
        
        # 응답 형식 확인
        assert "answer" in response
        assert "sources" in response
        assert isinstance(response["sources"], list)
    
    def test_context_retrieval(self, rag_service):
        """컨텍스트 검색 테스트"""
        # 검색 결과 직접 모킹
        search_results = [
            MagicMock(payload={"text": "관련 내용 1", "source": "doc1.pdf", "page": 1}, score=0.9),
            MagicMock(payload={"text": "관련 내용 2", "source": "doc1.pdf", "page": 2}, score=0.8)
        ]
        
        # _retrieve_context 메서드 접근 (실제 구현에 따라 다를 수 있음)
        with patch.object(rag_service, '_search_similar_chunks', return_value=search_results):
            context, sources = rag_service._retrieve_context("테스트 질문")
            
            # 컨텍스트 형식 확인
            assert isinstance(context, str)
            assert "관련 내용 1" in context
            assert "관련 내용 2" in context
            
            # 소스 정보 확인
            assert len(sources) == 2
            assert sources[0]["source"] == "doc1.pdf"
    
    def test_empty_query_handling(self, rag_service):
        """빈 쿼리 처리 테스트"""
        response = rag_service.query("")
        
        # 에러 응답 형식 확인
        assert "error" in response
    
    def test_no_results_handling(self, rag_service, mock_qdrant_client):
        """검색 결과 없음 처리 테스트"""
        # 빈 검색 결과 모킹
        mock_qdrant_client.search.return_value = []
        
        response = rag_service.query("관련 없는 질문")
        
        # 응답에 검색 결과 없음 메시지 포함 확인
        assert "no_results" in response or "answer" in response
        
        if "answer" in response:
            # 모델이 기본 응답 생성 확인
            assert response["answer"] is not None
            assert response["sources"] == [] 