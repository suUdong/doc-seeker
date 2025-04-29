from typing import Dict, Any, Optional, List
import os
from pathlib import Path
import logging

from ctransformers import AutoModelForCausalLM

from app.domain.services.llm_service import LLMService
from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger("infrastructure.llm.llama_service")

class LlamaService(LLMService):
    """
    LLaMA 모델을 사용하는 LLM 서비스 구현체
    ctransformers 라이브러리를 사용하여 로컬에서 LLaMA 모델을 실행합니다.
    """
    
    def __init__(self, config: AppConfig):
        """
        Args:
            config: 애플리케이션 설정
        """
        self.config = config
        self.model_path = config.MODEL_PATH
        self.model = None
        self._load_model()
        logger.info(f"LlamaService 초기화 완료: {self.model_path}")
    
    def _load_model(self) -> None:
        """
        모델을 로드합니다.
        """
        if not os.path.exists(self.model_path):
            error_msg = f"모델 파일이 존재하지 않습니다: {self.model_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            logger.info(f"모델 로딩 시작: {self.model_path}")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                model_type="llama",
                context_length=2048,  # 컨텍스트 길이 (문서 길이가 길 경우 조정 필요)
                threads=int(os.getenv("OMP_NUM_THREADS", "1")),  # 스레드 수
                gpu_layers=0  # GPU 사용하지 않음 (CPU 모드)
            )
            logger.info("모델 로딩 완료")
        except Exception as e:
            logger.exception(f"모델 로딩 실패: {e}")
            raise RuntimeError(f"모델 로딩 실패: {e}")
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 512, 
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        주어진 프롬프트를 기반으로 텍스트를 생성합니다.
        
        Args:
            prompt: 생성의 기반이 되는 프롬프트 텍스트
            max_tokens: 생성할 최대 토큰 수
            temperature: 생성 다양성 조절 파라미터
            top_p: 확률 분포에서 상위 p%의 토큰만 샘플링
            stop: 생성을 중지할 토큰 목록
            
        Returns:
            생성된 텍스트
        """
        if self.model is None:
            logger.warning("모델이 로드되지 않았습니다. 다시 로드합니다.")
            self._load_model()
        
        try:
            logger.debug(f"생성 시작: 토큰 수={max_tokens}, 온도={temperature}")
            
            # 모델에 제공할 스톱 토큰 설정
            stop_tokens = stop or []
            
            # 텍스트 생성
            generated_text = self.model(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop_tokens,
                stream=False  # 스트리밍 비활성화
            )
            
            # 프롬프트 제거 (모델에 따라 프롬프트가 출력에 포함될 수 있음)
            result = generated_text.replace(prompt, "", 1)
            
            logger.debug(f"생성 완료: 길이={len(result)}")
            return result.strip()
            
        except Exception as e:
            logger.exception(f"텍스트 생성 중 오류 발생: {e}")
            return f"텍스트 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        현재 사용 중인 모델에 대한 정보를 반환합니다.
        
        Returns:
            모델 정보가 포함된 딕셔너리
        """
        model_filename = Path(self.model_path).name
        
        return {
            "model_name": model_filename,
            "model_path": self.model_path,
            "model_type": "llama",
            "context_length": 2048,
            "loaded": self.model is not None
        } 