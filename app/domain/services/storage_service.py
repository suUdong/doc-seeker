from abc import ABC, abstractmethod
from typing import Tuple, Optional
import io

class StorageService(ABC):
    """
    파일 저장소 인터페이스
    
    파일 업로드, 다운로드, 삭제와 같은 저장소 작업에 대한 추상화 인터페이스입니다.
    특정 저장소 구현(로컬, S3 등)에 의존하지 않도록 도메인 계층에 정의합니다.
    """
    
    @abstractmethod
    async def save_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        파일을 저장소에 저장합니다.
        
        Args:
            file_content: 파일 내용 (바이트)
            filename: 원본 파일 이름
            
        Returns:
            Tuple[str, str]: 저장된 파일의 식별자(경로 또는 키)와 원본 파일명
            
        Raises:
            Exception: 파일 저장 중 오류 발생 시
        """
        pass
    
    @abstractmethod
    async def read_file(self, identifier: str) -> bytes:
        """
        주어진 식별자로 파일 내용을 읽어옵니다.
        
        Args:
            identifier: 파일 식별자 (경로 또는 키)
            
        Returns:
            bytes: 파일 내용
            
        Raises:
            FileNotFoundError: 파일을 찾을 수 없을 때
            Exception: 파일 읽기 중 오류 발생 시
        """
        pass
    
    @abstractmethod
    async def delete_file(self, identifier: str) -> bool:
        """
        주어진 식별자의 파일을 삭제합니다.
        
        Args:
            identifier: 파일 식별자 (경로 또는 키)
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass 