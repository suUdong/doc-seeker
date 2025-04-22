import os
import time
from ctransformers import AutoModelForCausalLM
from pathlib import Path

# 중앙화된 로깅 설정 사용
from .logger import get_logger
logger = get_logger('model_manager')

class ModelManager:
    """
    LLM 모델의 로딩, 관리, 정보 제공을 담당하는 클래스
    """
    
    # 모델 설정
    MODEL_NAME = "EleutherAI/polyglot-ko-1.3b"
    MODEL_TYPE = "llama"
    
    def __init__(self):
        # Docker 환경에서는 /app/models 경로 사용
        if os.path.exists('/app/models'):
            self.model_dir = "/app/models"
        else:
            # 로컬 개발 환경에서는 상대 경로 사용
            self.model_dir = os.path.join(os.path.dirname(__file__), "../models")
            
        # 디렉토리가 없으면 생성
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)
            
        self.model_path = os.path.join(self.model_dir, "polyglot-ko-1.3b.gguf")
        self.model = None
        
    def load_model(self):
        """모델을 로드하고 모델 객체를 반환합니다."""
        if self.model is not None:
            return self.model
            
        logger.info(f"{self.MODEL_NAME} 모델 로딩 시작")
        start_time = time.time()
        
        # 모델 파일이 없으면 다운로드 시도
        if not os.path.exists(self.model_path):
            logger.warning(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
            try:
                # 다운로드 스크립트 임포트 및 실행
                from .download_model import download_and_convert_model
                logger.info("모델 다운로드 및 변환을 시도합니다...")
                download_and_convert_model(self.MODEL_NAME, self.model_dir)
            except Exception as e:
                logger.error(f"모델 다운로드 실패: {str(e)}")
                logger.info("모델을 수동으로 다운로드하려면 다음 명령어를 실행하세요:")
                logger.info(f"python app/download_model.py --model {self.MODEL_NAME} --output {self.model_dir}")
                return None
            
        # 모델 로딩
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                model_type=self.MODEL_TYPE,
                config={'max_new_tokens': 512, 'temperature': 0.7, 'context_length': 2048}
            )
            logger.info(f"모델 로딩 완료: {time.time() - start_time:.2f}초 소요")
            return self.model
        except Exception as e:
            logger.error(f"모델 로딩 실패: {str(e)}")
            return None
    
    def get_model_info(self) -> dict:
        """모델 정보를 반환합니다."""
        if self.model is None:
            self.load_model()
            
        info = {
            "model_name": self.MODEL_NAME,
            "model_type": self.MODEL_TYPE,
            "model_path": self.model_path,
            "loaded": self.model is not None,
        }
        logger.info(f"모델 정보 요청: {info}")
        return info
        
    def is_model_loaded(self) -> bool:
        """모델이 로드되었는지 여부를 반환합니다."""
        return self.model is not None

# 싱글톤 인스턴스
model_manager = ModelManager() 