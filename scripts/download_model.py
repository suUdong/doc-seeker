#!/usr/bin/env python
import os
import sys
import argparse
import shutil
import subprocess
import logging
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download

# 로깅 설정 (스크립트 실행 시 사용)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('model_downloader_script')

DEFAULT_MODEL_DIR = "./models" # 프로젝트 루트 기준 models 폴더
DEFAULT_GGUF_DIR = "./models/gguf" # GGUF 모델용 디렉토리

def download_gguf_model(model_name, output_dir=DEFAULT_GGUF_DIR, skip_if_exists=True):
    """
    GGUF 포맷 모델을 HuggingFace에서 다운로드합니다.
    
    Args:
        model_name (str): HuggingFace 모델 이름
        output_dir (str): GGUF 모델을 저장할 디렉토리 경로
        skip_if_exists (bool): 해당 경로에 모델 파일이 이미 존재하면 다운로드를 건너뛸지 여부
    """
    # 모델 파일명을 정의
    gguf_filename = "polyglot-ko-1.3b.gguf"
    local_model_path = Path(output_dir) / gguf_filename

    logger.info(f"GGUF 모델 저장 경로 확인: {local_model_path.resolve()}")

    # 디렉토리 및 파일 존재 확인
    if skip_if_exists and local_model_path.exists():
        logger.info(f"GGUF 모델 파일이 이미 존재합니다: {local_model_path}")
        return str(local_model_path)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"HuggingFace에서 GGUF 모델 다운로드 시작: {model_name} -> {local_model_path}")
    try:
        # GGUF 모델 파일 직접 다운로드 
        # 참고: 실제 repo_id와 filename은 필요에 따라 조정해야 함
        hf_hub_download(
            repo_id="TheBloke/polyglot-ko-1.3B-GGUF",  # GGUF 버전 레포
            filename="polyglot-ko-1.3b.q4_0.gguf",  # 실제 파일명 (크기가 작은 quantized 버전 선택)
            local_dir=output_dir,
            local_dir_use_symlinks=False,
        )
        
        # 필요에 따라 다운로드된 파일명을 원하는 이름으로 변경
        downloaded_file = Path(output_dir) / "polyglot-ko-1.3b.q4_0.gguf"
        if downloaded_file.exists() and downloaded_file != local_model_path:
            shutil.move(str(downloaded_file), str(local_model_path))
        
        logger.info(f"GGUF 모델 다운로드 및 저장 완료: {local_model_path}")
        return str(local_model_path)

    except Exception as e:
        logger.error(f"GGUF 모델 다운로드 실패: {e}")
        return None  # 실패 시 None 반환

def download_model(model_name, output_dir=DEFAULT_MODEL_DIR, skip_if_exists=True):
    """
    HuggingFace 모델을 지정된 디렉토리에 다운로드합니다.
    
    Args:
        model_name (str): HuggingFace 모델 이름 (예: sentence-transformers/all-MiniLM-L6-v2)
        output_dir (str): 모델을 저장할 디렉토리 경로
        skip_if_exists (bool): 해당 경로에 모델 파일이 이미 존재하면 다운로드를 건너뛸지 여부
    """
    # 모델 이름에서 경로로 사용하기 안전한 이름 만들기 (예: / -> -)
    safe_model_name = model_name.replace("/", "-")
    local_model_path = Path(output_dir) / safe_model_name

    logger.info(f"모델 저장 경로 확인: {local_model_path.resolve()}")

    # 디렉토리 존재 및 내용 확인 (skip_if_exists가 True일 때)
    if skip_if_exists and local_model_path.exists() and any(local_model_path.iterdir()):
        logger.info(f"모델 디렉토리가 이미 로컬 경로에 존재하며 비어있지 않습니다: {local_model_path}")
        return str(local_model_path)

    logger.info(f"HuggingFace에서 모델 다운로드 시작: {model_name} -> {local_model_path}")
    try:
        # 임시 디렉토리에 먼저 다운로드 후 이동 (원자성 보장)
        temp_dir = local_model_path.with_suffix('.temp')
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            
        snapshot_download(
            repo_id=model_name, 
            local_dir=str(temp_dir),
            local_dir_use_symlinks=False, # Windows 호환성
            # revision="main", # 특정 브랜치/태그 지정 가능
            # allow_patterns=["*.bin", "*.json", "*.model"], # 특정 파일만 다운로드
            # ignore_patterns=["*.safetensors", "*.onnx"], # 특정 파일 제외
            # cache_dir=os.getenv("HF_HOME") or Path.home() / ".cache" / "huggingface" / "hub" # 캐시 디렉토리 지정 (선택 사항)
        )
        
        # 기존 디렉토리 삭제 후 이동
        if local_model_path.exists():
            shutil.rmtree(local_model_path)
        shutil.move(str(temp_dir), str(local_model_path))
        
        logger.info(f"모델 다운로드 및 저장 완료: {local_model_path}")
        return str(local_model_path)

    except Exception as e:
        logger.error(f"모델 다운로드 실패 ({model_name}): {e}")
        # 실패 시 임시 디렉토리 정리
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                logger.warning(f"임시 디렉토리 삭제 실패: {temp_dir}")
        return None # 실패 시 None 반환

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HuggingFace 모델 다운로드 스크립트")
    parser.add_argument(
        "--model", 
        type=str, 
        # 기본 모델을 polyglot-ko-1.3b 로 변경
        default="EleutherAI/polyglot-ko-1.3b", 
        help="다운로드할 HuggingFace 모델 이름 (예: google/gemma-2b-it)"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=DEFAULT_MODEL_DIR,
        help=f"모델을 저장할 디렉토리 (기본값: {DEFAULT_MODEL_DIR})"
    )
    parser.add_argument(
        "--gguf-dir", 
        type=str, 
        default=DEFAULT_GGUF_DIR,
        help=f"GGUF 모델을 저장할 디렉토리 (기본값: {DEFAULT_GGUF_DIR})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="모델 디렉토리가 이미 존재해도 강제로 다시 다운로드합니다."
    )
    parser.add_argument(
        "--gguf-only",
        action="store_true",
        help="GGUF 모델만 다운로드합니다."
    )
    
    args = parser.parse_args()
    
    logger.info(f"모델 다운로드 요청 시작")
    
    # GGUF 디렉토리 경로 준비
    gguf_path = Path(args.gguf_dir)
    if not gguf_path.is_absolute():
        gguf_path = Path.cwd() / gguf_path
    logger.info(f"GGUF 저장 위치: {gguf_path.resolve()}")
    
    # GGUF 모델 다운로드
    gguf_downloaded_path = download_gguf_model(
        args.model,
        str(gguf_path),
        skip_if_exists=not args.force
    )
    
    if gguf_downloaded_path:
        logger.info(f"GGUF 모델 다운로드 완료: {gguf_downloaded_path}")
    else:
        logger.error("GGUF 모델 다운로드 실패")
        sys.exit(1)
    
    # 일반 모델 다운로드 (--gguf-only가 지정되지 않은 경우)
    if not args.gguf_only:
        # output_dir 인자가 절대 경로가 아니면, 스크립트 실행 위치 기준으로 경로 해석
        output_path = Path(args.output_dir)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        logger.info(f"일반 모델 저장 위치: {output_path.resolve()}")
        
        downloaded_path = download_model(
            args.model, 
            str(output_path),
            skip_if_exists=not args.force
        )
        
        if downloaded_path:
            logger.info(f"일반 모델 다운로드 완료: {downloaded_path}")
        else:
            logger.error("일반 모델 다운로드 실패")
            if gguf_downloaded_path:
                logger.info("GGUF 모델은 다운로드 성공, 계속 진행합니다.")
            else:
                sys.exit(1)
    
    logger.info(f"스크립트 실행 완료. GGUF 모델 위치: {gguf_downloaded_path}")
    sys.exit(0) 