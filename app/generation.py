import os
import time

# 중앙화된 로깅 설정 사용
from .logger import get_logger
logger = get_logger('generation')

# 모델 매니저 임포트
from .model_manager import model_manager

# 프롬프트 템플릿
PROMPT_TEMPLATE = """다음 정보를 참고하여 질문에 답변해주세요.

참고 정보:
{context}

질문: {query}

답변:"""

class LLMGenerator:
    def __init__(self):
        """LLM 생성기 초기화"""
        # 모델 매니저를 통해 모델 로드
        self.model = model_manager.load_model()
    
    def generate(self, query: str, context_chunks: list[str], max_tokens: int = 512) -> str:
        """
        주어진 질문과 컨텍스트를 기반으로 응답을 생성합니다.
        
        Args:
            query: 사용자 질문
            context_chunks: RAG에서 검색된 관련 문서 청크 목록
            max_tokens: 생성할 최대 토큰 수
            
        Returns:
            생성된 응답 텍스트
        """
        # 모델이 로드되지 않았다면 다시 시도
        if self.model is None:
            self.model = model_manager.load_model()
            
        if self.model is None:
            return "모델이 로드되지 않았습니다. 모델 파일을 다운로드하고 다시 시도해주세요."
            
        # 로그 남기기
        logger.info(f"응답 생성 시작 - 질문: {query[:50]}..." if len(query) > 50 else query)
        logger.debug(f"컨텍스트: {len(context_chunks)}개 청크, 총 {sum(len(chunk) for chunk in context_chunks)}자")
        
        start_time = time.time()
        
        # 컨텍스트 합치기 (너무 길면 자르기)
        context_text = "\n\n".join(context_chunks)
        
        # 프롬프트 생성
        prompt = PROMPT_TEMPLATE.format(
            context=context_text,
            query=query
        )
        
        try:
            # 응답 생성
            response = self.model(
                prompt, 
                max_new_tokens=max_tokens,
                temperature=0.7,
                repetition_penalty=1.1,
                top_p=0.9,
                stream=False
            )
            
            # 생성 후처리
            generated_text = response
            
            elapsed_time = time.time() - start_time
            logger.info(f"응답 생성 완료: 길이 {len(generated_text)}자, 소요시간 {elapsed_time:.2f}초")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return f"오류가 발생했습니다: {str(e)}"
    
    def get_model_info(self) -> dict:
        """모델 정보를 반환합니다."""
        return model_manager.get_model_info()

# 싱글톤 인스턴스
generator = LLMGenerator()

def generate_response(query: str, context_chunks: list[str], max_tokens: int = 512) -> str:
    """
    사용자 쿼리와 검색된 컨텍스트를 바탕으로 응답을 생성합니다.
    """
    return generator.generate(query, context_chunks, max_tokens) 