import pytest
import os
import tempfile
import requests
from fastapi.testclient import TestClient
from app.main import app

class TestIntegration:
    """통합 테스트"""
    
    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_document(self):
        """샘플 PDF 문서 생성"""
        # ASCII 문자만 사용하는 간단한 PDF 구조
        content = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 24 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test Document) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000198 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n293\n%%EOF"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(content)
            path = f.name
        
        yield path
        
        # 테스트 후 파일 삭제
        if os.path.exists(path):
            os.remove(path)
    
    def test_health_check(self, client):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_document_upload_and_query(self, client, sample_document):
        """문서 업로드 및 질의 통합 테스트"""
        # 1. 문서 업로드
        with open(sample_document, "rb") as f:
            files = {"file": (os.path.basename(sample_document), f, "application/pdf")}
            upload_response = client.post("/documents/upload/", files=files)
        
        assert upload_response.status_code == 200
        assert upload_response.json()["success"] is True
        document_id = upload_response.json().get("document_id")
        assert document_id is not None
        
        # 인덱싱 완료 대기 (실제 시스템에서는 더 긴 시간이 필요할 수 있음)
        import time
        time.sleep(2)
        
        # 2. 질의 수행
        query_data = {"query": "이 문서는 무엇에 관한 것입니까?"}
        query_response = client.post("/query/", json=query_data)
        
        assert query_response.status_code == 200
        assert "answer" in query_response.json()
    
    def test_document_listing(self, client, sample_document):
        """문서 목록 조회 테스트"""
        # 먼저 문서 업로드
        with open(sample_document, "rb") as f:
            files = {"file": (os.path.basename(sample_document), f, "application/pdf")}
            client.post("/documents/upload/", files=files)
        
        # 문서 목록 조회
        response = client.get("/documents/")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        # 적어도 하나의 문서가 있어야 함
        assert len(response.json()) > 0
        
        # 문서 속성 확인
        document = response.json()[0]
        assert "id" in document
        assert "filename" in document
        assert "upload_date" in document
    
    def test_error_handling(self, client):
        """에러 처리 테스트"""
        # 1. 잘못된 파일 형식으로 업로드
        with tempfile.NamedTemporaryFile(suffix=".xyz") as f:
            f.write(b"invalid content")
            f.flush()
            files = {"file": (os.path.basename(f.name), open(f.name, "rb"), "application/octet-stream")}
            response = client.post("/documents/upload/", files=files)
        
        # 적절한 에러 응답 확인
        assert response.status_code in [400, 415, 422]  # 클라이언트 에러
        assert "error" in response.json()
        
        # 2. 빈 쿼리 테스트
        query_data = {"query": ""}
        response = client.post("/query/", json=query_data)
        
        assert response.status_code in [400, 422]  # 클라이언트 에러
        assert "error" in response.json()
    
    @pytest.mark.skipif(not os.environ.get("RUN_LIVE_TESTS"), reason="라이브 테스트 건너뜀")
    def test_live_server(self):
        """실제 서버에 대한 테스트 (선택적)"""
        base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        
        # 헬스 체크
        response = requests.get(f"{base_url}/health/")
        assert response.status_code == 200
        
        # 간단한 질의
        query_data = {"query": "안녕하세요"}
        response = requests.post(f"{base_url}/query/", json=query_data)
        assert response.status_code == 200 