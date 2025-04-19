# 기본 Python 이미지 사용
FROM python:3.10-slim

# 작업 디렉터리
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드
RUN pip install --upgrade pip

# 의존성 설치
COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# 앱 소스 복사
COPY app/ ./app/

# 스레드 관련 환경 변수 설정 - 호환성 문제 해결
ENV OMP_NUM_THREADS=1
ENV PYTHONUNBUFFERED=1

# FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]