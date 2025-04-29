from abc import ABC, abstractmethod
from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.logger import get_logger
from app.core.config import AppConfig

logger = get_logger("infrastructure.embedding")

class EmbeddingService(ABC):
    """임베딩 서비스 인터페이스
    
    텍스트 임베딩을 생성하는 인터페이스입니다.
    """
    
    @abstractmethod
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """텍스트 임베딩 생성"""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """여러 텍스트 임베딩 생성 (배치 처리)"""
        pass
    
    @abstractmethod
    def get_vector_size(self) -> int:
        """임베딩 벡터 크기 반환"""
        pass

class SentenceTransformerEmbedding(EmbeddingService):
    """SentenceTransformer 기반 임베딩 서비스 구현체"""
    
    def __init__(self, config: AppConfig):
        self.model_name = config.EMBEDDING_MODEL_ID
        
        try:
            # 모델 로드
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"SentenceTransformer 모델 로드 완료: {self.model_name}")
        except Exception as e:
            logger.exception(f"SentenceTransformer 모델 로드 실패: {e}")
            raise
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """텍스트 임베딩 생성"""
        if not text or text.isspace():
            logger.warning("임베딩할 텍스트가 비어있습니다.")
            return None
        
        try:
            # 임베딩 생성
            embedding = self.model.encode(text)
            
            # numpy 배열을 리스트로 변환
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            return embedding
        except Exception as e:
            logger.exception(f"텍스트 임베딩 생성 중 오류: {e}")
            return None
    
    async def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """여러 텍스트 임베딩 생성 (배치 처리)"""
        if not texts:
            logger.warning("임베딩할 텍스트가 없습니다.")
            return None
        
        # 빈 텍스트 필터링
        valid_texts = [text for text in texts if text and not text.isspace()]
        if not valid_texts:
            logger.warning("임베딩할 유효한 텍스트가 없습니다.")
            return None
        
        try:
            # 배치 임베딩 생성
            embeddings = self.model.encode(valid_texts)
            
            # numpy 배열을 리스트로 변환
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            return embeddings
        except Exception as e:
            logger.exception(f"텍스트 배치 임베딩 생성 중 오류: {e}")
            return None
    
    def get_vector_size(self) -> int:
        """임베딩 벡터 크기 반환"""
        return self.model.get_sentence_embedding_dimension() 