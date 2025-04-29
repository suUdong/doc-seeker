import os
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에 .env 파일이 있는 경우)
# load_dotenv()

# 스토리지 설정
# STORAGE_TYPE: 'local' 또는 's3' (추후 다른 클라우드 지원 확장 가능)
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
# 로컬 스토리지 경로 (STORAGE_TYPE='local' 일 때 사용)
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "uploaded_files")

# AWS S3 설정 (STORAGE_TYPE='s3' 일 때 사용)
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
# AWS 자격증명은 환경 변수나 EC2/ECS 역할 등을 통해 관리하는 것을 권장
# S3_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# S3_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# 파일 크기 제한 (단위: MB)
# 0 또는 음수 값은 제한 없음을 의미
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100")) # 기본 100MB 제한

# Qdrant 설정
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "documents")
# QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") # API 키가 필요한 경우
# QDRANT_BATCH_SIZE = int(os.getenv("QDRANT_BATCH_SIZE", 100))
# QDRANT_SCORE_THRESHOLD = float(os.getenv("QDRANT_SCORE_THRESHOLD", 0.7))

# 모델 설정
MODEL_BASE_PATH = os.getenv("MODEL_BASE_PATH", "./models") # 모델 파일 기본 저장 경로 (최상위 models/)

# 임베딩 모델 설정
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
# EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 32))

# 생성 모델(LLM) 설정
GENERATION_MODEL_TYPE = os.getenv("GENERATION_MODEL_TYPE", "transformers").lower() # 'transformers' or 'gguf'
GENERATION_MODEL_ID = os.getenv("GENERATION_MODEL_ID", "EleutherAI/polyglot-ko-1.3b") # For 'transformers' type or download source
GENERATION_MODEL_GGUF_FILENAME = os.getenv("GENERATION_MODEL_GGUF_FILENAME", "polyglot-ko-1.3b-f16.gguf") # For 'gguf' type

# DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
# MAX_ANSWER_LENGTH = int(os.getenv("MAX_ANSWER_LENGTH", 512))
# GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", 0.7))
# GENERATION_TOP_P = float(os.getenv("GENERATION_TOP_P", 0.9))
# QA_PROMPT_TEMPLATE = os.getenv("QA_PROMPT_TEMPLATE", "Context:\\n{context}\\n\\nQuestion: {query}\\n\\nAnswer:")

# --- ctransformers (GGUF) 관련 설정 (필요시 추가) ---
# GPU_LAYERS = int(os.getenv("GPU_LAYERS", 0)) # GPU에 올릴 레이어 수 (0이면 CPU만 사용)
# CT_MAX_NEW_TOKENS = int(os.getenv("CT_MAX_NEW_TOKENS", 512))
# CT_TEMPERATURE = float(os.getenv("CT_TEMPERATURE", 0.7))
# CT_TOP_P = float(os.getenv("CT_TOP_P", 0.9))
# CT_CONTEXT_LENGTH = int(os.getenv("CT_CONTEXT_LENGTH", 2048)) # 모델의 컨텍스트 길이

# Pydantic Settings 사용을 위한 클래스 정의 (선택 사항이지만 권장)
# from pydantic_settings import BaseSettings
# class AppConfig(BaseSettings):
#     STORAGE_TYPE: str = "local"
#     LOCAL_STORAGE_PATH: str = "uploaded_files"
#     S3_BUCKET: Optional[str] = None
#     ...
#     MODEL_BASE_PATH: str = "./models"
#     EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"
#     GENERATION_MODEL_ID: str = "EleutherAI/polyglot-ko-1.3b"

#     class Config:
#         env_file = '.env'
#         env_file_encoding = 'utf-8'

# config = AppConfig() 