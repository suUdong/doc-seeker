# PyTorch가 사전 설치된 이미지 사용
FROM python:3.10-slim

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 시스템 패키지 및 컴파일러 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    gcc \
    libgomp1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 필수 패키지만 설치 (torch 등 모든 의존성 포함)
COPY requirements.txt .

# llama-cpp-python 바이너리 패키지 사용 (컴파일 필요 없음)
RUN pip install --no-cache-dir -r requirements.txt \
    ctransformers==0.2.27 \
    huggingface-hub==0.20.3 \
    --find-links https://github.com/jllllll/llama-cpp-python-cuBLAS-wheels/releases/download/textgen-webui/llama_cpp_python-0.2.55+cpuavx2-cp310-cp310-linux_x86_64.whl

# 모델 및 로그 디렉토리 생성
RUN mkdir -p models logs

# 애플리케이션 코드 복사
COPY app/ app/

# 엔트리포인트 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 환경 변수 설정
ENV OMP_NUM_THREADS=1 \
    PYTHONUNBUFFERED=1

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# 엔트리포인트 설정
ENTRYPOINT ["/app/entrypoint.sh"]

# FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]