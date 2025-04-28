import os
import sys
import time
from pathlib import Path
from huggingface_hub import snapshot_download, HfApi

def download_model():
    # 모델명 및 출력 디렉토리 설정
    model_name = "EleutherAI/polyglot-ko-1.3b"
    output_dir = Path("models") / "polyglot-ko-1.3b"
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"모델 {model_name}을(를) {output_dir}에 다운로드합니다...")
    
    max_retries = 3
    current_retry = 0
    
    while current_retry < max_retries:
        try:
            # Hugging Face에서 모델 다운로드
            snapshot_download(
                repo_id=model_name,
                local_dir=str(output_dir),
                local_dir_use_symlinks=False,
                max_workers=1  # 동시 다운로드 수 제한
            )
            print(f"모델 다운로드 완료! 위치: {output_dir}")
            return True
        except Exception as e:
            current_retry += 1
            if current_retry < max_retries:
                wait_time = current_retry * 5  # 재시도 간격 점진적 증가
                print(f"다운로드 실패 ({current_retry}/{max_retries}): {e}")
                print(f"{wait_time}초 후 재시도합니다...")
                time.sleep(wait_time)
            else:
                print(f"모든 재시도 실패: {e}")
                print("\n수동 다운로드 방법:")
                print(f"1. 브라우저에서 https://huggingface.co/{model_name}/tree/main 방문")
                print("2. 다음 파일들을 다운로드하여 'models/polyglot-ko-1.3b' 폴더에 저장:")
                print("   - config.json")
                print("   - pytorch_model.bin (가장 중요, 약 1.3GB)")
                print("   - tokenizer.json")
                print("   - tokenizer_config.json")
                print("\n또는 Git LFS를 사용한 다운로드 방법:")
                print("1. Git LFS 설치 (https://git-lfs.github.com/)")
                print("2. 다음 명령어 실행:")
                print(f"   git lfs install")
                print(f"   git clone https://huggingface.co/{model_name} {output_dir}")
                return False

def download_files_individually():
    """개별 파일 다운로드 시도"""
    model_name = "EleutherAI/polyglot-ko-1.3b"
    output_dir = Path("models") / "polyglot-ko-1.3b"
    os.makedirs(output_dir, exist_ok=True)
    
    print("개별 파일 다운로드를 시도합니다...")
    
    try:
        # HF API 초기화
        api = HfApi()
        
        # 중요 파일 목록
        files = [
            "config.json",
            "pytorch_model.bin",
            "tokenizer.json",
            "tokenizer_config.json"
        ]
        
        # 각 파일 다운로드
        for file in files:
            print(f"{file} 다운로드 중...")
            try:
                api.hf_hub_download(
                    repo_id=model_name,
                    filename=file,
                    local_dir=str(output_dir),
                    local_dir_use_symlinks=False
                )
                print(f"- {file} 다운로드 완료")
            except Exception as e:
                print(f"- {file} 다운로드 실패: {e}")
        
        return True
    except Exception as e:
        print(f"개별 파일 다운로드 실패: {e}")
        return False

if __name__ == "__main__":
    # pip install huggingface-hub 확인
    try:
        import huggingface_hub
        if not download_model():
            print("\n전체 모델 다운로드 실패. 개별 파일 다운로드를 시도합니다...")
            download_files_individually()
    except ImportError:
        print("huggingface-hub 패키지가 필요합니다.")
        print("설치하려면: pip install huggingface-hub")
        sys.exit(1) 