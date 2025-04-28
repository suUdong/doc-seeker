# Service for managing language models (Loading, Embeddings, Generation)
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import os
import time
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Union

# Import from new core locations
from app.core.config import AppConfig # Use AppConfig
from app.core.logger import get_logger

logger = get_logger("service.model_manager")

class ModelManager:
    """모델 관리 클래스 (서비스 계층)"""
    
    def __init__(self, config: AppConfig):
        """
        ModelManager 초기화
        
        Args:
            config: 애플리케이션 설정 객체 (AppConfig)
        """
        self.config = config
        # TODO: Update config attributes if names changed (e.g., MODEL_PATH might not exist)
        # self.model_path = self.config.GENERATION_MODEL_PATH or "default/model/path" 
        # self.embedding_model_name = self.config.EMBEDDING_MODEL_NAME or "default-embedding-model"
        self.model_path = os.getenv("MODEL_PATH", "models/default_llm") # Example: Get from env
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2") # Example
        
        self.model = None
        self.tokenizer = None
        self.embedding_model = None
        # TODO: Get device from config if defined there
        self.device = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """임베딩 모델 로드"""
        try:
            logger.info(f"임베딩 모델 로드 중: {self.embedding_model_name}")
            # Consider adding try-except around SentenceTransformer for robustness
            self.embedding_model = SentenceTransformer(self.embedding_model_name, device=self.device)
            # No need to call .to(self.device) separately if specified in constructor
            logger.info(f"임베딩 모델 로드 완료 ({self.device})")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 중 오류 발생: {str(e)}")
            raise
    
    def _ensure_llm_loaded(self):
        """텍스트 생성 모델(LLM)이 로드되었는지 확인하고 필요시 로드"""
        if self.model is not None and self.tokenizer is not None:
            return

        logger.info(f"텍스트 생성 모델(LLM) 로드 시도: {self.model_path}")
        try:
            if not os.path.isdir(self.model_path):
                 logger.error(f"LLM 모델 경로를 찾을 수 없습니다: {self.model_path}")
                 raise FileNotFoundError(f"Model path not found: {self.model_path}")

            start_time = time.time()
            # Always load tokenizer first
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            logger.info(f"토크나이저 로드 완료 ({time.time() - start_time:.2f}초)")
            
            # Load the main model
            # TODO: Add configuration for torch_dtype based on device/config
            dtype = torch.float16 if self.device == "cuda" else torch.float32 
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=dtype
            ).to(self.device)
            logger.info(f"LLM 모델 로드 완료 ({self.device}, {time.time() - start_time:.2f}초)")

        except Exception as e:
            logger.error(f"LLM 모델 또는 토크나이저 로드 중 오류 발생: {str(e)}")
            # Reset to None on failure
            self.model = None
            self.tokenizer = None
            raise
    
    async def get_embeddings(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[List[float]], None]:
        """
        텍스트의 임베딩 생성 (비동기 처리 고려, 모델 따라 sync/async)
        SentenceTransformer.encode is CPU-bound, so running in executor might be needed for true async.
        However, keeping it simple for now.
        
        Args:
            text: 임베딩할 텍스트 또는 텍스트 리스트
            
        Returns:
            np.ndarray or List[List[float]] or None: 임베딩 벡터(들)
        """
        if self.embedding_model is None:
            logger.error("임베딩 모델이 로드되지 않았습니다.")
            return None
            
        try:
            is_single_string = isinstance(text, str)
            texts_to_encode = [text] if is_single_string else text
            
            # TODO: Get batch size from config
            # batch_size = self.config.EMBEDDING_BATCH_SIZE
            batch_size = 32 # Example batch size

            embeddings = self.embedding_model.encode(
                texts_to_encode, 
                convert_to_numpy=True, 
                batch_size=batch_size, 
                show_progress_bar=False # Disable progress bar for logs
            )
            
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            # Avoid division by zero for zero-vectors (though unlikely for text embeddings)
            norms[norms == 0] = 1e-12
            embeddings_norm = embeddings / norms
            
            if is_single_string:
                return embeddings_norm[0] # Return single numpy array
            else:
                return embeddings_norm.tolist() # Return list of lists for Qdrant

        except Exception as e:
            logger.exception(f"임베딩 생성 중 오류 발생: {e}") # Use exception for traceback
            return None
    
    async def generate_text(self, prompt: str, max_length: int = 512, temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        주어진 프롬프트에서 텍스트 생성 (비동기)
        Model generation can be blocking, consider running in a thread pool executor for true async.
        
        Args:
            prompt: 생성의 시작점
            max_length: 최대 생성 길이
            temperature: 생성 다양성
            top_p: Top-p 샘플링
            
        Returns:
            str: 생성된 텍스트 또는 오류 메시지
        """
        try:
            self._ensure_llm_loaded() # 로드 확인 및 필요시 로드
            if self.model is None or self.tokenizer is None:
                 return "오류: 텍스트 생성 모델을 로드할 수 없습니다."

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True, # Ensure sampling is enabled for temp/top_p
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Optional: Clean up prompt from the beginning of the generated text if needed
            if generated_text.startswith(prompt):
                 generated_text = generated_text[len(prompt):].lstrip()
                 
            return generated_text
            
        except Exception as e:
            logger.exception(f"텍스트 생성 중 오류 발생: {e}")
            return f"죄송합니다. 응답 생성 중 오류 발생: {str(e)}"

# Note: The get_model_manager dependency function in core/dependencies.py
# should be updated to initialize and return this ModelManager class, injecting AppConfig. 