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

# 모델 설정
# 필요한 모델 관련 설정 추가 가능
# EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "...")
# GENERATION_MODEL_NAME = os.getenv("GENERATION_MODEL_NAME", "...") 