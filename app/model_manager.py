from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import os
import time
import logging
from sentence_transformers import SentenceTransformer

# 로깅 설정
from app.logger import get_logger
logger = get_logger("model_manager")

class ModelManager:
    """모델 관리 클래스"""
    
    # 기본 모델 설정
    MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"
    MODEL_PATH = "/app/models/polyglot-ko-1.3b"
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    def __init__(self, model_path=None):
        """
        ModelManager 초기화
        
        Args:
            model_path: 모델 경로 (기본값: None, 기본 경로 사용)
        """
        self.model_path = model_path or self.MODEL_PATH
        self.model = None
        self.tokenizer = None
        self.embedding_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 임베딩 모델 로드 (더 가볍고 빠름)
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """임베딩 모델 로드"""
        try:
            logger.info(f"임베딩 모델 로드 중: {self.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
            logger.info("임베딩 모델 로드 완료")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 중 오류 발생: {str(e)}")
            raise
    
    def load_model(self):
        """모델 및 토크나이저 로드 (필요시에만)"""
        # 이미 로드된 경우 스킵
        if self.model is not None:
            return
            
        try:
            # 모델 경로 설정
            model_path = self.model_path
            
            # 디렉토리가 존재하는지 확인
            if os.path.isdir(model_path):
                logger.info(f"모델 로드 중: {model_path}")
                start_time = time.time()
                
                # 토크나이저만 먼저 로드
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                logger.info(f"토크나이저 로드 완료 ({time.time() - start_time:.2f}초)")
                
                # 필요할 때 전체 모델 로드 (지연 로딩)
                # self.model = AutoModelForCausalLM.from_pretrained(
                #     model_path,
                #     torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                # ).to(self.device)
                
                logger.info(f"모델 지연 로딩 설정 완료 (디바이스: {self.device})")
            else:
                logger.error(f"모델 디렉토리가 존재하지 않습니다: {model_path}")
        
        except Exception as e:
            logger.error(f"모델 로드 중 오류 발생: {str(e)}")
            raise
    
    def get_embeddings(self, text):
        """
        텍스트의 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            numpy.ndarray: 임베딩 벡터
        """
        try:
            # SentenceTransformer를 사용하여 임베딩 생성 (더 빠르고 최적화됨)
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            
            # 정규화
            embedding_norm = embedding / np.linalg.norm(embedding)
            
            return embedding_norm
            
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {str(e)}")
            raise
    
    def generate_text(self, prompt, max_length=100, temperature=0.7):
        """
        주어진 프롬프트에서 텍스트 생성
        
        Args:
            prompt: 생성의 시작점
            max_length: 최대 생성 길이
            temperature: 생성 다양성 (높을수록 다양함)
            
        Returns:
            str: 생성된 텍스트
        """
        try:
            # 모델이 로드되지 않았으면 로드
            if self.model is None:
                logger.info("텍스트 생성을 위해 전체 모델 로드 중...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                ).to(self.device)
                logger.info("전체 모델 로드 완료")
            
            # 토크나이저가 로드되지 않았으면 로드
            if self.tokenizer is None:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # 텍스트 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 디코딩하여 텍스트 반환
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text
            
        except Exception as e:
            logger.error(f"텍스트 생성 중 오류 발생: {str(e)}")
            # 간단한 대체 응답 제공
            return f"죄송합니다. 응답을 생성하는 중 오류가 발생했습니다: {str(e)}"

# 싱글톤 인스턴스
model_manager = ModelManager() 