# 🧪 테스트 아키텍처

doc-seeker는 강력한 다층적 테스트 아키텍처를 갖추고 있습니다. 이 문서는 테스트 전략, 구조 및 실행 방법을 설명합니다.

## 테스트 아키텍처 개요

doc-seeker의 테스트는 다음 세 가지 계층으로 구성됩니다:

```
┌─────────────────────────────────┐
│     엔드투엔드 테스트 (E2E)      │ - API 엔드포인트 및 전체 시스템 흐름
├─────────────────────────────────┤
│         통합 테스트             │ - 모듈 간 상호작용
├─────────────────────────────────┤
│         단위 테스트             │ - 개별 기능 단위
└─────────────────────────────────┘
```

## 단위 테스트

단위 테스트는 개별 모듈과 클래스의 기능을 검증합니다.

### 임베딩 테스트 (`test_embedding.py`)

임베딩 모듈의 핵심 기능 검증:

- 모델 로딩 검증
- 임베딩 벡터 생성 및 정규화 검증
- 동일 텍스트의 일관성 검증
- 유사 텍스트 간 의미적 유사도 검증
- 한글 처리 능력 검증

```python
def test_embedding_creation(self, model_manager):
    """텍스트 임베딩 생성 테스트"""
    test_text = "이것은 임베딩 테스트를 위한 텍스트입니다."
    embedding = model_manager.get_embeddings(test_text)

    # 임베딩 벡터 형태 확인
    assert isinstance(embedding, np.ndarray), "임베딩 결과가 numpy 배열이 아닙니다."
    assert embedding.ndim == 1, "임베딩 결과가 1차원 벡터가 아닙니다."
    assert embedding.shape[0] > 0, "임베딩 벡터 차원이 0입니다."
```

## 통합 테스트

통합 테스트는 여러 모듈의 상호작용을 검증합니다.

### RAG 시스템 테스트 (`test_rag.py`)

RAG(Retrieval-Augmented Generation) 시스템의 작동 검증:

- 문서 인덱싱 기능 검증
- 질의 처리 파이프라인 검증
- 컨텍스트 검색 정확도 검증
- 에러 케이스 처리 검증

```python
def test_query_processing(self, rag_service, mock_model_manager, mock_qdrant_client):
    """질의 처리 테스트"""
    query = "테스트 질문입니다"
    response = rag_service.query(query)

    # 임베딩이 생성되었는지 확인
    mock_model_manager.get_embeddings.assert_called_with(query)

    # Qdrant 검색이 호출되었는지 확인
    mock_qdrant_client.search.assert_called_once()
```

## 엔드투엔드 테스트

엔드투엔드 테스트는 API 엔드포인트와 전체 시스템 흐름을 검증합니다.

### 통합 테스트 (`test_integration.py`)

FastAPI 엔드포인트 및 전체 시스템 검증:

- 헬스체크 엔드포인트 검증
- 문서 업로드-인덱싱-질의 전체 흐름 검증
- 문서 관리 기능 검증
- 에러 처리 및 예외 상황 검증
- 실제 서버 연동 테스트(선택적)

```python
def test_document_upload_and_query(self, client, sample_document):
    """문서 업로드 및 질의 통합 테스트"""
    # 1. 문서 업로드
    with open(sample_document, "rb") as f:
        files = {"file": (os.path.basename(sample_document), f, "application/pdf")}
        upload_response = client.post("/documents/upload/", files=files)

    assert upload_response.status_code == 200
    assert upload_response.json()["success"] is True
```

## 테스트 실행 방법

### 모든 테스트 실행

```bash
pytest -v
```

### 특정 테스트 모듈 실행

```bash
pytest -v tests/test_embedding.py
pytest -v tests/test_rag.py
pytest -v tests/test_integration.py
```

### 특정 테스트 함수 실행

```bash
pytest -v tests/test_rag.py::TestRAG::test_query_processing
```

### 옵션 테스트 실행 (환경변수 이용)

```bash
# 라이브 서버 테스트 활성화
RUN_LIVE_TESTS=1 pytest -v tests/test_integration.py::TestIntegration::test_live_server
```

## 테스트 모킹 전략

외부 의존성을 효과적으로 모킹하기 위해 다음 전략을 사용합니다:

1. **Qdrant 클라이언트 모킹**: 벡터 DB 의존성 격리
2. **ModelManager 모킹**: 임베딩 및 생성 모델 격리
3. **파일 시스템 모킹**: 임시 파일 사용으로 실제 파일 시스템 격리

```python
@pytest.fixture
def mock_qdrant_client(self):
    """Qdrant 클라이언트 모킹"""
    mock_client = MagicMock()

    # search 메서드 모킹
    search_result = [
        MagicMock(payload={"text": "테스트 문서 내용 1"}, score=0.95),
        MagicMock(payload={"text": "테스트 문서 내용 2"}, score=0.85)
    ]
    mock_client.search.return_value = search_result

    return mock_client
```

## 지속적 통합 (CI) 전략

GitHub Actions 또는 Jenkins를 사용한 CI 파이프라인 구성 권장:

1. 모든 PR에 대해 단위 테스트 및 통합 테스트 실행
2. 메인 브랜치 병합 시 전체 테스트 스위트 실행
3. 정기적인 야간 테스트 실행으로 시스템 안정성 확인

## 테스트 커버리지

테스트 커버리지 확인을 위해 pytest-cov 사용 권장:

```bash
pytest --cov=app tests/
```

## 테스트 모범 사례

1. 각 테스트는 독립적이고 격리되어야 함
2. 테스트는 빠르게 실행되어야 함 (느린 테스트는 별도 표시)
3. 적절한 어설션 메시지로 실패 원인 명확히 제공
4. 테스트 픽스처를 효과적으로 활용하여 중복 최소화
5. 환경 의존성을 최소화하고 모킹으로 대체
