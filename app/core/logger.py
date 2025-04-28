import os
import logging
from logging.handlers import RotatingFileHandler

# 로그 디렉토리 설정
LOG_DIR = os.environ.get("LOG_DIR", "/app/logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# 로거 포맷 설정
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    로거 인스턴스 생성
    
    Args:
        name: 로거 이름
        level: 로깅 레벨
        
    Returns:
        logging.Logger: 로거 인스턴스
    """
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 로거가 이미 핸들러를 가지고 있으면 기존 핸들러 유지
    if logger.handlers:
        return logger
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_format)
    
    # 파일 핸들러 추가
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_format = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_format)
    
    # 핸들러 등록
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 미리 정의된 로거들
app_logger = get_logger('app')
model_logger = get_logger('model_manager')
generation_logger = get_logger('generation')
embedding_logger = get_logger('embedding')
retrieval_logger = get_logger('retrieval')

# 로거 가져오기 함수
def get_named_logger(name):
    """
    이름으로 로거 가져오기
    
    Args:
        name: 로거 이름
        
    Returns:
        logger: 로거 인스턴스
    """
    # 미리 정의된 로거 중에서 찾기
    predefined = {
        'app': app_logger,
        'model_manager': model_logger,
        'generation': generation_logger,
        'embedding': embedding_logger,
        'retrieval': retrieval_logger
    }
    
    if name in predefined:
        return predefined[name]
    else:
        # 정의되지 않은 이름은, 새 로거 생성
        return get_logger(name) 