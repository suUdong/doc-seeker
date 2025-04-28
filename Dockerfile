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

# pip 설정 파일 생성 - 타임아웃 증가 및 재시도 설정
RUN mkdir -p /root/.config/pip && \
    echo "[global]\ntimeout = 600\nretries = 10\ntrusted-host = files.pythonhosted.org pypi.org" > /root/.config/pip/pip.conf

# 패키지 분할 설치 (안정성 향상)
# 먼저 필수 패키지 설치
RUN pip install pip --upgrade && \
    pip install setuptools wheel

# --- PyTorch CPU 버전 명시적 설치 시작 ---
# requirements.txt 처리 전에 PyTorch CPU 버전을 설치하여 CUDA 패키지 다운로드 방지
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
# --- PyTorch CPU 버전 명시적 설치 끝 ---

# requirements.txt 에서 나머지 패키지 설치 (torch는 이미 CPU 버전으로 설치됨)
RUN pip install -r requirements.txt

# 추가 패키지 설치 (이 부분은 필요에 따라 requirements.txt로 옮기는 것을 고려)
RUN pip install ctransformers==0.2.27 huggingface-hub==0.20.3

# llama-cpp-python 패키지 설치 (별도 명령으로 분리)
RUN pip install llama-cpp-python==0.2.55 --find-links https://github.com/jllllll/llama-cpp-python-cuBLAS-wheels/releases/download/textgen-webui/llama_cpp_python-0.2.55+cpuavx2-cp310-cp310-linux_x86_64.whl || \
    pip install llama-cpp-python==0.2.55

# 모델 및 로그 디렉토리 생성
RUN mkdir -p models logs

# 애플리케이션 코드 복사
COPY app/ app/
# 스크립트 폴더 복사
COPY scripts/ scripts/

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