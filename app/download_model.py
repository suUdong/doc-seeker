#!/usr/bin/env python
import os
import sys
import argparse
import shutil
import subprocess
import logging
from pathlib import Path
from huggingface_hub import snapshot_download

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('model_downloader')

def download_and_convert_model(model_name, output_path):
    """
    HuggingFace 모델을 다운로드하고 GGUF 형식으로 변환
    
    Args:
        model_name (str): HuggingFace 모델 이름 (예: EleutherAI/polyglot-ko-1.3b)
        output_path (str): 출력 GGUF 파일 경로
    """
    # 출력 디렉토리 생성
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 이미 GGUF 파일이 존재하는지 확인
    if os.path.exists(output_path):
        logger.info(f"모델 파일이 이미 존재합니다: {output_path}")
        return

    # 로컬 모델 디렉토리 설정
    local_model_dir = "/app/models/polyglot-ko-1.3b"
    
    # 이미 모델 디렉토리가 존재하는지 확인
    if os.path.exists(local_model_dir) and os.path.isfile(os.path.join(local_model_dir, "pytorch_model.bin")):
        logger.info(f"로컬에 이미 모델 파일이 있습니다: {local_model_dir}")
    else:
        # 임시 디렉토리 설정
        temp_dir = "/app/models/temp_hf_model"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        try:
            # HuggingFace에서 모델 다운로드
            logger.info(f"모델 다운로드 중: {model_name}")
            snapshot_download(
                repo_id=model_name, 
                local_dir=temp_dir, 
                local_dir_use_symlinks=False
            )
            
            # 다운로드한 모델을 최종 위치로 이동
            if os.path.exists(local_model_dir):
                shutil.rmtree(local_model_dir)
            shutil.move(temp_dir, local_model_dir)
            
            logger.info("모델 다운로드 완료")
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {str(e)}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return
    
    # GGUF 변환 건너뛰기 (모델을 원본 형식으로 사용)
    logger.info("원본 모델을 직접 사용합니다 (GGUF 변환 건너뜀)")
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HuggingFace 모델을 다운로드하고 GGUF로 변환")
    parser.add_argument("--model", type=str, default="EleutherAI/polyglot-ko-1.3b", help="HuggingFace 모델 이름")
    parser.add_argument("--output", type=str, default="/app/models/polyglot-ko-1.3b.gguf", help="출력 GGUF 파일 경로")
    
    args = parser.parse_args()
    
    download_and_convert_model(args.model, args.output) 