import os
import shutil
import uuid
from typing import Tuple
import aiofiles

from app.domain.services.storage_service import StorageService
from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger("infrastructure.storage.local")

class LocalStorageService(StorageService):
    """
    로컬 파일 시스템 저장소 구현체
    
    로컬 파일 시스템을 사용하여 파일을 저장하고 관리합니다.
    """
    
    def __init__(self, config: AppConfig):
        """
        Args:
            config: 애플리케이션 설정
        """
        self.config = config
        self.storage_path = config.LOCAL_STORAGE_PATH
        # 저장 경로가 없으면 생성
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"로컬 저장소 초기화 완료: {self.storage_path}")
    
    async def save_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        파일을 로컬 저장소에 저장합니다.
        
        Args:
            file_content: 파일 내용 (바이트)
            filename:
            
        Returns:
            Tuple[str, str]: 파일 경로와 원본 파일명
        """
        try:
            # 파일 확장자 추출
            file_extension = os.path.splitext(filename)[1].lower()
            # 고유 ID 생성
            unique_id = str(uuid.uuid4())
            # 저장할 파일명 생성
            saved_filename = f"{unique_id}{file_extension}"
            # 전체 파일 경로
            file_path = os.path.join(self.storage_path, saved_filename)
            
            # 비동기로 파일 저장
            async with aiofiles.open(file_path, "wb") as buffer:
                await buffer.write(file_content)
            
            logger.info(f"파일 로컬 저장 완료: {file_path}")
            return file_path, filename
            
        except Exception as e:
            logger.error(f"로컬 파일 저장 실패 ({filename}): {e}")
            raise Exception(f"로컬 파일 저장 실패: {e}")
    
    async def read_file(self, identifier: str) -> bytes:
        """
        로컬 저장소에서 파일을 읽어옵니다.
        
        Args:
            identifier: 파일 경로
            
        Returns:
            bytes: 파일 내용
        """
        file_path = identifier  # 로컬에서는 식별자가 파일 경로
        
        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                logger.error(f"로컬 파일을 찾을 수 없습니다: {file_path}")
                raise FileNotFoundError(f"로컬 파일을 찾을 수 없습니다: {file_path}")
            
            # 비동기로 파일 읽기
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            
            logger.debug(f"로컬 파일 로드 완료: {file_path}")
            return content
            
        except FileNotFoundError:
            # 이미 처리됨
            raise
        except Exception as e:
            logger.error(f"로컬 파일 읽기 실패 ({file_path}): {e}")
            raise Exception(f"로컬 파일 읽기 실패: {e}")
    
    async def delete_file(self, identifier: str) -> bool:
        """
        로컬 저장소에서 파일을 삭제합니다.
        
        Args:
            identifier: 파일 경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        file_path = identifier
        
        try:
            # 파일이 존재하는지 확인하고 삭제
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"로컬 파일 삭제 완료: {file_path}")
                return True
            else:
                logger.warning(f"삭제할 로컬 파일 없음: {file_path}")
                return False  # 파일이 없어도 실패는 아님
                
        except OSError as e:
            logger.warning(f"로컬 파일 삭제 실패 ({file_path}): {e}")
            return False
        except Exception as e:
            logger.error(f"로컬 파일 삭제 중 예상치 못한 오류: {e}")
            return False 