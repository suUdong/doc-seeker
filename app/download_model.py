#!/usr/bin/env python
import os
import subprocess
import argparse
from pathlib import Path

# 중앙화된 로깅 설정 사용
try:
    # 직접 실행 시에는 상대 경로 임포트가 불가능하므로 예외 처리
    from app.logger import get_logger
    logger = get_logger('model_downloader')
except ImportError:
    # 직접 실행 시 로깅 기본 설정
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('model_downloader')

# 기본 모델 설정 - model_manager와 일관성 유지
try:
    # 직접 임포트가 안될 경우를 대비한 예외 처리
    from app.model_manager import ModelManager
    default_model_name = ModelManager.MODEL_NAME
except ImportError:
    default_model_name = "EleutherAI/polyglot-ko-1.3b"

def download_and_convert_model(model_name=default_model_name, output_dir="/app/models"):
    """
    Hugging Face에서 모델을 다운로드하고 GGUF로 변환합니다.
    
    Args:
        model_name: Hugging Face 모델 이름
        output_dir: 출력 디렉토리 경로
    """
    # 출력 디렉토리 생성
    model_dir = Path(output_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 모델 기본 이름 추출 (뒤의 부분만)
    model_base_name = model_name.split('/')[-1]
    gguf_path = model_dir / f"{model_base_name}.gguf"
    
    # 이미 변환된 모델이 있는지 확인
    if gguf_path.exists():
        logger.info(f"이미 변환된 모델이 존재합니다: {gguf_path}")
        return str(gguf_path)
    
    # 임시 디렉토리 생성
    temp_dir = model_dir / "temp_hf_model"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Hugging Face에서 모델 다운로드
        logger.info(f"Hugging Face에서 {model_name} 모델 다운로드 중...")
        subprocess.run([
            "python", "-m", "huggingface_hub", "download", 
            model_name, 
            "--local-dir", str(temp_dir),
            "--local-dir-use-symlinks", "False"
        ], check=True)
        
        # 2. GGUF로 변환
        logger.info(f"모델을 GGUF 형식으로 변환 중...")
        
        # 변환 도구 설치 확인
        try:
            subprocess.run(["pip", "install", "llama-cpp-python"], check=True)
        except subprocess.CalledProcessError:
            logger.error("llama-cpp-python 설치 실패")
            raise
            
        try:
            # llama.cpp의 변환 도구 사용
            subprocess.run([
                "python", "-m", "llama_cpp.model_converter", 
                "--model", str(temp_dir),
                "--output", str(gguf_path),
                "--type", "f16"  # 절반 정밀도로 변환
            ], check=True)
        except Exception as e:
            logger.error(f"GGUF 변환 실패: {str(e)}")
            raise
            
        logger.info(f"모델 변환 완료: {gguf_path}")
        return str(gguf_path)
        
    except Exception as e:
        logger.error(f"모델 다운로드 또는 변환 중 오류 발생: {str(e)}")
        raise
    finally:
        # 임시 파일 정리 (선택 사항)
        # import shutil
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hugging Face 모델을 다운로드하고 GGUF로 변환")
    parser.add_argument("--model", default=default_model_name, help="Hugging Face 모델 이름")
    parser.add_argument("--output", default="/app/models", help="출력 디렉토리")
    
    args = parser.parse_args()
    download_and_convert_model(args.model, args.output) 