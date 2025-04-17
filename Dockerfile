# 1) 베이스 이미지
FROM python:3.10-slim

# 2) 작업 디렉터리
WORKDIR /app

# 3) 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --verbose -r requirements.txt && \
    pip list

# 4) 앱 소스 복사
COPY app/ ./app/

# 5) FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
