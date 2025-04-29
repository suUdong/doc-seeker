from app.domain.services.storage_service import StorageService
from app.infrastructure.storage.local_storage_service import LocalStorageService
from app.infrastructure.storage.s3_storage_service import S3StorageService
from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger("infrastructure.storage.factory")

def get_storage_service(config: AppConfig) -> StorageService:
    """
    설정에 따라 적절한 StorageService 구현체를 반환합니다.
    
    Args:
        config: 애플리케이션 설정
        
    Returns:
        StorageService: 저장소 서비스 구현체
        
    Raises:
        ValueError: 지원하지 않는 저장소 유형일 경우
    """
    storage_type = config.STORAGE_TYPE
    logger.info(f"저장소 유형: {storage_type}")
    
    if storage_type == "local":
        return LocalStorageService(config)
    elif storage_type == "s3":
        return S3StorageService(config)
    else:
        error_msg = f"지원하지 않는 저장소 유형입니다: {storage_type}"
        logger.error(error_msg)
        raise ValueError(error_msg) 