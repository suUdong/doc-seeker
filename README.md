# doc-seeker

doc-seeker는 기업용 문서 검색 및 QA(질의응답) 시스템입니다. Qdrant를 벡터 저장소로 사용하는 RAG(Retrieval-Augmented Generation)를 지원하며 다양한 임베딩 모델과 통합되어 향후 LLM 기반 응답을 위한 기반을 마련합니다.

## ✨ 주요 기능

- 문서 업로드 및 임베딩 (텍스트 기반)
- 저장된 청크에 대한 의미 검색
- sentence-transformers를 이용한 임베딩 (예: E5, KoSimCSE)
- FastAPI 기반 마이크로서비스
- 벡터 저장 및 검색을 위한 Qdrant
- sLLM 또는 vLLM(DeepSeek, Mistral 등)과의 LLM 통합 계획
- Docker 기반 아키텍처, 확장 가능한 설계

## ⚡ 아키텍처 개요

```
[Slack/Teams/...]
↓
[FastAPI App] <---- REST API
├── /ingest : 문서 수집 (임베딩 + 인덱싱)
├── /query : 의미적 유사성을 통한 검색
└── /generate : (계획) LLM을 통한 답변 생성
↓
[Embedding Module] (sentence-transformers)
↓
[Qdrant] (벡터 DB)
↓
[LLM Inference Layer] ← sLLM (CPU) 또는 vLLM (GPU) 백엔드
```

향후 계획: LLM 생성 모듈(vLLM/Ollama), 사용자 RBAC, 파이프라인 DAG 자동화.

## 📂 프로젝트 구조

```
doc-seeker/
├── app/
│   ├── main.py       # FastAPI 진입점
│   ├── embeddings.py # 임베딩 유틸리티
│   ├── api/          # (계획) API 라우터
│   ├── pipelines/    # (계획) 수집 단계
│   └── db/           # (선택) 향후 RDB 통합
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔍 사용 예시

**문서 수집**

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"title": "Doc1", "text": "...some content..."}'
```

**검색**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "search phrase", "top_k": 5}'
```

## 🌐 임베딩 모델

HuggingFace 호환 모델 지원:

- **intfloat/multilingual-e5-base** — 다국어, 강력한 검색 성능
- **jominai/KoSimCSE-roberta** — 한국어 중심 의미적 유사성
- **(플러그형)** FastAPI 전환 가능한 임베딩 모듈

## 🧠 LLM 통합 계획

유사 콘텐츠 검색 후 응답 생성을 위해 LLM이 통합될 예정입니다. 두 가지 런타임 옵션:

| 유형 | 도구               | 비고               |
| ---- | ------------------ | ------------------ |
| sLLM | DeepSeek, KoAlpaca | 로컬 CPU 수준 추론 |
| vLLM | vllm-project/vllm  | 고성능, GPU 지원   |

이들은 다음과 같은 페이로드로 /generate 엔드포인트(계획)를 통해 사용될 예정입니다:

```json
{
  "query": "업무 일정이 어떻게 되나요?",
  "context": ["문서 청크1", "문서 청크2"]
}
```

## 🛠 배포

**요구사항:**

- Docker, Docker Compose

**실행:**

```bash
docker-compose up --build -d
```

**포트:**

- FastAPI: http://localhost:8000
- Qdrant: http://localhost:6333

## 🧪 테스트

프로젝트는 다층적 테스트 아키텍처를 갖추고 있습니다:

- 단위 테스트: 개별 모듈 기능 검증
- 통합 테스트: 모듈 간 상호작용 검증
- 엔드투엔드 테스트: 전체 시스템 검증

상세한 테스트 정보는 [README_TEST.md](README_TEST.md)를 참조하세요.

## 🌟 로드맵 (기업 준비도)

## 🚫 라이센스

내부 기업용으로만 사용 가능.

## 🙏 기여자

doc-seeker 팀이 ❤️로 만들었습니다.

## 🔗 관련 프로젝트

- [Qdrant](https://qdrant.tech/)
- [sentence-transformers](https://www.sbert.net/)
- [Prefect](https://www.prefect.io/)
- [vLLM](https://github.com/vllm-project/vllm)
