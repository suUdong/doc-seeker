import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에 .env 파일이 있는 경우)
load_dotenv()

# 환경 변수
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")  # local, dev, test, prod
ENV_PROFILE = os.getenv("ENV_PROFILE", "standard")  # light, standard, performance

class AppConfig(BaseSettings):
    """애플리케이션 전체 설정
    
    환경(local, dev, prod)과 프로필(light, standard, performance)에 따라
    적절한 설정을 제공합니다.
    """

    # 기본 앱 설정
    APP_NAME: str = "doc-seeker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = ENVIRONMENT != "prod"

    # 환경 및 프로필 설정
    ENVIRONMENT: str = ENVIRONMENT
    ENV_PROFILE: str = ENV_PROFILE  # 새로 추가된 프로필 개념

    # 스토리지 설정
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "uploaded_files")
    
    # AWS S3 설정 (STORAGE_TYPE='s3' 일 때 사용)
    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET")
    S3_REGION: Optional[str] = os.getenv("S3_REGION")
    
    # 파일 크기 제한 (단위: MB)
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))  # 기본 100MB 제한

    # Qdrant 설정
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "documents")
    QDRANT_SCORE_THRESHOLD: float = float(os.getenv("QDRANT_SCORE_THRESHOLD", "0.7"))

    # 모델 설정
    MODEL_BASE_PATH: str = os.getenv("MODEL_BASE_PATH", "./models")

    # 임베딩 모델 설정 - 프로필에 따라 자동 설정
    EMBEDDING_MODEL_ID: str = os.getenv("EMBEDDING_MODEL_ID", "")  # 초기값은 비워두고 프로필 기반으로 설정
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    # 생성 모델(LLM) 설정 - 프로필에 따라 자동 설정
    GENERATION_MODEL_TYPE: str = os.getenv("GENERATION_MODEL_TYPE", "").lower()  # 'transformers' or 'gguf'
    GENERATION_MODEL_ID: str = os.getenv("GENERATION_MODEL_ID", "")  # 프로필 기반으로 설정
    GENERATION_MODEL_GGUF_FILENAME: str = os.getenv("GENERATION_MODEL_GGUF_FILENAME", "")  # 프로필 기반으로 설정

    # LLM 생성 설정
    MAX_ANSWER_LENGTH: int = int(os.getenv("MAX_ANSWER_LENGTH", "512"))
    GENERATION_TEMPERATURE: float = float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
    GENERATION_TOP_P: float = float(os.getenv("GENERATION_TOP_P", "0.9"))
    
    # GGUF 설정 (ctransformers)
    GPU_LAYERS: int = int(os.getenv("GPU_LAYERS", "0"))  # 프로필에 따라 달라짐
    CT_CONTEXT_LENGTH: int = int(os.getenv("CT_CONTEXT_LENGTH", "2048"))
    CT_MAX_NEW_TOKENS: int = int(os.getenv("CT_MAX_NEW_TOKENS", "512"))
    CT_TEMPERATURE: float = float(os.getenv("CT_TEMPERATURE", "0.7"))
    CT_TOP_P: float = float(os.getenv("CT_TOP_P", "0.9"))

    # 챗봇 설정
    QA_PROMPT_TEMPLATE: str = os.getenv(
        "QA_PROMPT_TEMPLATE", 
        "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._apply_profile_settings()
    
    def _apply_profile_settings(self):
        """환경 프로필에 따른 설정 적용"""
        # 프로필별 기본 설정
        profile_settings = {
            "light": {
                # 경량 모델 설정 (노트북, CPU 환경용)
                "EMBEDDING_MODEL_ID": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "GENERATION_MODEL_TYPE": "gguf",
                "GENERATION_MODEL_ID": "EleutherAI/polyglot-ko-1.3b",
                "GENERATION_MODEL_GGUF_FILENAME": "polyglot-ko-1.3b.q4_0.gguf",
                "GPU_LAYERS": 0,  # CPU만 사용
                "CT_CONTEXT_LENGTH": 1024,  # 컨텍스트 길이 축소
                "MAX_ANSWER_LENGTH": 256  # 답변 길이 축소
            },
            "standard": {
                # 표준 모델 설정 (일반 환경용)
                "EMBEDDING_MODEL_ID": "sentence-transformers/all-MiniLM-L6-v2",
                "GENERATION_MODEL_TYPE": "gguf",
                "GENERATION_MODEL_ID": "EleutherAI/polyglot-ko-1.3b",
                "GENERATION_MODEL_GGUF_FILENAME": "polyglot-ko-1.3b.gguf",
                "GPU_LAYERS": 0,  # CPU 우선, 환경에 따라 자동 조정
                "CT_CONTEXT_LENGTH": 2048
            },
            "performance": {
                # 고성능 모델 설정 (서버, GPU 환경용)
                "EMBEDDING_MODEL_ID": "sentence-transformers/all-mpnet-base-v2",
                "GENERATION_MODEL_TYPE": "transformers",  # HF Transformers 사용
                "GENERATION_MODEL_ID": "EleutherAI/polyglot-ko-5.8b",
                "GPU_LAYERS": 32,  # 가능한 많은 레이어를 GPU에 로드
                "CT_CONTEXT_LENGTH": 4096
            }
        }
        
        # 프로필 설정 적용 (환경 변수로 설정되지 않은 항목만)
        profile = self.ENV_PROFILE.lower()
        if profile in profile_settings:
            settings = profile_settings[profile]
            
            # 환경 변수로 설정되지 않은 값만 기본값으로 설정
            for key, value in settings.items():
                if not os.getenv(key):
                    setattr(self, key, value)
                    
        # 환경에 따른 추가 설정 (예: prod 환경에서는 디버그 비활성화)
        if self.ENVIRONMENT == "prod":
            self.DEBUG = False

    def to_dict(self) -> Dict[str, Any]:
        """설정을 사전 형태로 변환"""
        return {
            key: getattr(self, key) 
            for key in self.__annotations__.keys()
        }

    def get_model_path(self) -> Path:
        """현재 설정에 맞는 모델 경로 반환"""
        if self.GENERATION_MODEL_TYPE == "gguf":
            return Path(self.MODEL_BASE_PATH) / "gguf" / self.GENERATION_MODEL_GGUF_FILENAME
        else:
            # transformers의 경우 모델 ID를 안전한 디렉토리 이름으로 변환
            safe_model_name = self.GENERATION_MODEL_ID.replace("/", "-")
            return Path(self.MODEL_BASE_PATH) / safe_model_name

    def get_embedding_path(self) -> Path:
        """임베딩 모델 경로 반환"""
        safe_model_name = self.EMBEDDING_MODEL_ID.replace("/", "-")
        return Path(self.MODEL_BASE_PATH) / safe_model_name 