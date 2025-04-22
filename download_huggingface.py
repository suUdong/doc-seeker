import subprocess
import os
from pathlib import Path

# 모델 설정
MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"
OUTPUT_DIR = "./models"

# 출력 디렉토리 생성
model_dir = Path(OUTPUT_DIR)
model_dir.mkdir(parents=True, exist_ok=True)

print(f"모델 다운로드 시작: {MODEL_NAME}")
print(f"출력 경로: {model_dir}")

# huggingface-cli 명령으로 다운로드
try:
    subprocess.run([
        "huggingface-cli", "download",
        MODEL_NAME,
        "--local-dir", str(model_dir),
        "--local-dir-use-symlinks", "False"
    ], check=True)
    print("모델 다운로드 완료!")
except Exception as e:
    print(f"huggingface-cli 오류: {e}")
    print("대체 방법으로 다운로드 시도...")
    
    # 실패하면 git clone으로 시도
    try:
        subprocess.run([
            "git", "clone", 
            f"https://huggingface.co/{MODEL_NAME}",
            str(model_dir / MODEL_NAME.split('/')[-1])
        ], check=True)
        print("git을 통한 다운로드 완료!")
    except Exception as e2:
        print(f"git 다운로드 오류: {e2}")
        print("수동으로 다운로드 해주세요:")
        print(f"1. https://huggingface.co/{MODEL_NAME} 방문")
        print("2. 'Files and versions' 탭 클릭")
        print("3. 모든 파일 다운로드 후 models 폴더에 저장")

print("\n모델 다운로드가 완료되었습니다.")
print("Docker 컨테이너 내부에서 자동으로 GGUF로 변환됩니다.")
print("docker-compose up --build 명령으로 시작하세요.") 