#!/usr/bin/env python
import os
import subprocess
from pathlib import Path

MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"
OUTPUT_DIR = "./models"

model_dir = Path(OUTPUT_DIR)
model_dir.mkdir(parents=True, exist_ok=True)

model_base_name = MODEL_NAME.split('/')[-1]
gguf_path = model_dir / f"{model_base_name}.gguf"

print(f"모델 다운로드 시작: {MODEL_NAME}")

temp_dir = model_dir / "temp_hf_model"
temp_dir.mkdir(exist_ok=True)

subprocess.run([
    "python", "-m", "huggingface_hub", "download", 
    MODEL_NAME, 
    "--local-dir", str(temp_dir),
    "--local-dir-use-symlinks", "False"
], check=True)

print("모델 다운로드 완료, GGUF 변환 시작...")

subprocess.run([
    "python", "-m", "llama_cpp.model_converter", 
    "--model", str(temp_dir),
    "--output", str(gguf_path),
    "--type", "f16"
], check=True)

print(f"변환 완료! 파일 경로: {gguf_path}") 