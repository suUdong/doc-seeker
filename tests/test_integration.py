import pytest
import os
import tempfile
import requests
import time

# 기본 API URL 설정
BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

class TestIntegration:
    """통합 테스트 (requests 사용)"""
    
    @pytest.fixture
    def sample_document(self):
        """샘플 TXT 문서 생성"""
        # 간단한 텍스트 내용
        content = "이것은 샘플 텍스트 문서입니다.\n두 번째 줄입니다."

        # 임시 파일 생성 (접미사를 .txt로 변경)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w', encoding='utf-8') as f:
            f.write(content)
            path = f.name

        yield path

        # 테스트 후 파일 삭제
        if os.path.exists(path):
            os.remove(path)
    
    def test_health_check(self):
        """헬스 체크 엔드포인트 테스트"""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_document_upload_and_query(self, sample_document):
        """문서 업로드 및 질의 통합 테스트"""
        # 1. 문서 업로드 (client 대신 requests 사용)
        with open(sample_document, "rb") as f: # 'rb'로 읽는 것 유지 (requests files는 바이너리 필요)
            # content_type을 text/plain으로 명시
            files = {"file": (os.path.basename(sample_document), f, "text/plain")}
            upload_response = requests.post(f"{BASE_URL}/documents/upload/", files=files)

        assert upload_response.status_code == 200
        upload_json = upload_response.json()
        assert upload_json.get("success") is True
        document_id = upload_json.get("document_id")
        assert document_id is not None
        
        # 인덱싱 완료 대기
        time.sleep(2)
        
        # 2. 질의 수행 (client 대신 requests 사용)
        query_data = {"query": "이 문서는 무엇에 관한 것입니까?"}
        query_response = requests.post(f"{BASE_URL}/query/", json=query_data)
        
        assert query_response.status_code == 200
        assert "answer" in query_response.json()
    
    def test_document_listing(self, sample_document):
        """문서 목록 조회 테스트"""
        # 먼저 문서 업로드 (client 대신 requests 사용)
        with open(sample_document, "rb") as f:
             # content_type을 text/plain으로 명시
            files = {"file": (os.path.basename(sample_document), f, "text/plain")}
            requests.post(f"{BASE_URL}/documents/upload/", files=files)
            time.sleep(1) # 업로드 처리 시간 약간 대기
        
        # 문서 목록 조회
        response = requests.get(f"{BASE_URL}/documents/")
        
        assert response.status_code == 200
        response_json = response.json()
        assert isinstance(response_json, list)
        # 적어도 하나의 문서가 있어야 함 (목업 데이터가 아닌 실제 데이터 확인 필요)
        # 실제 데이터 확인 로직 추가 또는 목업 확인 유지
        assert len(response_json) > 0 # 현재 list_documents는 목업 반환
        
        # 문서 속성 확인 (목업 데이터 기반)
        document = response_json[0]
        assert "id" in document
        assert "filename" in document
        assert "upload_date" in document
    
    def test_error_handling(self):
        """에러 처리 테스트"""
        # 1. 잘못된 파일 형식으로 업로드 (client 대신 requests 사용)
        invalid_content = b"invalid content"
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=True) as f: # delete=True로 변경하여 자동 삭제
            f.write(invalid_content)
            f.flush() # 내용을 파일에 쓰도록 보장
            # 파일을 다시 열지 않고 파일 이름과 내용을 직접 사용
            files = {"file": (os.path.basename(f.name), invalid_content, "application/octet-stream")}
            # with 블록이 끝나면 파일이 자동으로 닫히고 삭제됨
            response = requests.post(f"{BASE_URL}/documents/upload/", files=files)

        # 적절한 에러 응답 확인
        assert response.status_code in [400, 415, 422]  # 클라이언트 에러
        assert "detail" in response.json()

        # 2. 빈 쿼리 테스트 (client 대신 requests 사용)
        query_data = {"query": ""}
        response = requests.post(f"{BASE_URL}/query/", json=query_data)

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