#!/bin/bash
set -e

echo "엔트리포인트 스크립트 실행 중..."

# 로그 디렉토리 생성
mkdir -p /app/logs

# 모델 디렉토리 생성
mkdir -p /app/models

# 모델 파일 존재 여부 확인 (model_manager.py의 경로와 일치하도록 확인)
MODEL_FILE="/app/models/polyglot-ko-1.3b.gguf"
if [ ! -f "$MODEL_FILE" ]; then
    echo "모델 파일이 없습니다. 다운로드를 시작합니다..."
    python /app/scripts/download_model.py
    if [ $? -ne 0 ]; then
        echo "모델 다운로드 실패! 오류를 확인하세요."
        exit 1
    fi
    echo "모델 다운로드 및 변환 완료!"
else
    echo "모델 파일이 이미 존재합니다. 다운로드를 건너뜁니다."
fi

# 원래 명령 실행
echo "애플리케이션 시작 중..."
exec "$@" 