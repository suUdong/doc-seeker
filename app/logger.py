import os
import logging
from pathlib import Path

# 로그 디렉토리 생성
log_dir = os.path.join(os.path.dirname(__file__), '../logs')
Path(log_dir).mkdir(parents=True, exist_ok=True)

# 로깅 포맷 정의
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logger(logger_name, log_file=None, level=logging.INFO):
    """
    로거를 설정하고 반환합니다.
    
    Args:
        logger_name: 로거 이름
        log_file: 로그 파일 이름 (없으면 콘솔만 사용)
        level: 로깅 레벨
        
    Returns:
        설정된
    """
    logger = logging.getLogger(logger_name)
    
    # 이미 핸들러가 설정된 경우 새로 설정하지 않음
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (파일명이 지정된 경우)
    if log_file:
        file_handler = logging.FileHandler(
            os.path.join(log_dir, log_file), 
            mode='a'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 로그가 상위 로거로 전파되지 않도록 설정
    logger.propagate = False
    
    return logger

# 미리 정의된 로거들
app_logger = setup_logger('app', 'app.log')
model_logger = setup_logger('model_manager', 'model_manager.log')
generation_logger = setup_logger('generation', 'generation.log')
embedding_logger = setup_logger('embedding', 'embedding.log')
retrieval_logger = setup_logger('retrieval', 'retrieval.log')

# 로거 가져오기 함수
def get_logger(name):
    """
    이름에 따라 미리 설정된 로거를 반환하거나, 새 로거를 생성합니다.
    """
    if name == 'app':
        return app_logger
    elif name == 'model_manager':
        return model_logger
    elif name == 'generation':
        return generation_logger
    elif name == 'embedding':
        return embedding_logger
    elif name == 'retrieval':
        return retrieval_logger
    else:
        # 정의되지 않은 이름은 새 로거 생성
        return setup_logger(name, f'{name}.log') 