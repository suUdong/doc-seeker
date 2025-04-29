from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMService(ABC):
    """
    LLM(Large Language Model) 서비스 인터페이스
    
    이 인터페이스는 언어 모델 생성 기능에 필요한 메서드를 정의합니다.
    """
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 512, 
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[list] = None
    ) -> str:
        """
        주어진 프롬프트를 기반으로 텍스트를 생성합니다.
        
        Args:
            prompt: 생성의 기반이 되는 프롬프트 텍스트
            max_tokens: 생성할 최대 토큰 수
            temperature: 생성 다양성 조절 파라미터 (높을수록 다양한 답변)
            top_p: 확률 분포에서 상위 p%의 토큰만 샘플링 (핵 샘플링)
            stop: 생성을 중지할 토큰 목록
            
        Returns:
            생성된 텍스트
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        현재 사용 중인 모델에 대한 정보를 반환합니다.
        
        Returns:
            모델 정보가 포함된 딕셔너리
        """
        pass 