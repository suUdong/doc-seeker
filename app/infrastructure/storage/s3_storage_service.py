import os
import uuid
from typing import Tuple
import boto3
from botocore.exceptions import ClientError
import io

from app.domain.services.storage_service import StorageService
from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger("infrastructure.storage.s3")

class S3StorageService(StorageService):
    """
    AWS S3 저장소 구현체
    
    AWS S3를 사용하여 파일을 저장하고 관리합니다.
    """
    
    def __init__(self, config: AppConfig):
        """
        Args:
            config: 애플리케이션 설정
        """
        self.config = config
        self.s3_bucket = config.S3_BUCKET
        if not self.s3_bucket:
            raise ValueError("S3 버킷이 설정되지 않았습니다. S3_BUCKET 환경변수를 확인하세요.")
            
        self.s3_region = config.S3_REGION
        logger.info(f"S3 저장소 초기화 완료: 버킷={self.s3_bucket}, 리전={self.s3_region}")
    
    def _get_s3_client(self):
        """
        S3 클라이언트를 가져옵니다.
        
        참고: 실제 환경에서는 보안을 위해 IAM 역할 등을 통한 인증 방식을 고려해야 합니다.
        """
        return boto3.client('s3', region_name=self.s3_region)
    
    async def save_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        파일을 S3에 저장합니다.
        
        Args:
            file_content: 파일 내용 (바이트)
            filename: 원본 파일명
            
        Returns:
            Tuple[str, str]: S3 키와 원본 파일명
        """
        try:
            # 파일 확장자 추출
            file_extension = os.path.splitext(filename)[1].lower()
            # 고유 ID 생성
            unique_id = str(uuid.uuid4())
            # S3 키 생성
            s3_key = f"uploads/{unique_id}{file_extension}"
            
            # S3 클라이언트 가져오기
            s3 = self._get_s3_client()
            
            # 메모리 버퍼 생성
            buffer = io.BytesIO(file_content)
            
            # S3에 업로드
            s3.upload_fileobj(
                buffer,
                self.s3_bucket,
                s3_key
            )
            
            logger.info(f"파일 S3 업로드 완료: s3://{self.s3_bucket}/{s3_key}")
            return s3_key, filename
            
        except ClientError as e:
            logger.error(f"S3 업로드 실패: {e}")
            raise Exception(f"S3 업로드 실패: {e}")
        except Exception as e:
            logger.error(f"S3 처리 중 예상치 못한 오류: {e}")
            raise Exception(f"S3 처리 중 오류 발생: {e}")
    
    async def read_file(self, identifier: str) -> bytes:
        """
        S3에서 파일을 읽어옵니다.
        
        Args:
            identifier: S3 키
            
        Returns:
            bytes: 파일 내용
        """
        s3_key = identifier  # S3에서는 식별자가 S3 키
        
        try:
            # S3 클라이언트 가져오기
            s3 = self._get_s3_client()
            
            # S3에서 객체 가져오기
            s3_object = s3.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = s3_object['Body'].read()
            
            logger.debug(f"S3 파일 다운로드 완료: s3://{self.s3_bucket}/{s3_key}")
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"S3 파일을 찾을 수 없습니다: s3://{self.s3_bucket}/{s3_key}")
                raise FileNotFoundError(f"S3 파일을 찾을 수 없습니다: s3://{self.s3_bucket}/{s3_key}")
            else:
                logger.error(f"S3 파일 다운로드 실패: {e}")
                raise Exception(f"S3 파일 다운로드 실패: {e}")
        except Exception as e:
            logger.error(f"S3 처리 중 예상치 못한 오류: {e}")
            raise Exception(f"S3 처리 중 오류 발생: {e}")
    
    async def delete_file(self, identifier: str) -> bool:
        """
        S3에서 파일을 삭제합니다.
        
        Args:
            identifier: S3 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        s3_key = identifier
        
        try:
            # S3 클라이언트 가져오기
            s3 = self._get_s3_client()
            
            # S3에서 객체 삭제
            s3.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            
            logger.debug(f"S3 객체 삭제 완료: s3://{self.s3_bucket}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.warning(f"S3 객체 삭제 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"S3 삭제 처리 중 예상치 못한 오류: {e}")
            return False 