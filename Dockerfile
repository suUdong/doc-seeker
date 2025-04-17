# 기본 Python 이미지 사용
FROM python:3.10-slim

# 작업 디렉터리
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 앱 소스 복사
COPY app/ ./app/

# FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]