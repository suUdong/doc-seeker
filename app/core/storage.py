import os
import shutil
import uuid
from abc import ABC, abstractmethod
from typing import Protocol, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.config import Config
from app.logger import get_logger

logger = get_logger("storage")

class StorageHandler(Protocol):
    """파일 저장소 작업을 위한 인터페이스 정의 (프로토콜)"""

    config: Config

    def save_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        업로드된 파일을 저장소에 저장하고 파일 식별자와 원본 파일명을 반환합니다.

        Args:
            file: FastAPI의 UploadFile 객체.

        Returns:
            Tuple[str, str]: 저장된 파일의 고유 식별자 (경로 또는 키)와 원본 파일명.

        Raises:
            Exception: 파일 저장 중 오류 발생 시.
        """
        ...

    def read_file(self, identifier: str) -> bytes:
        """
        주어진 식별자를 사용하여 파일 내용을 읽어옵니다.

        Args:
            identifier: 파일 식별자 (경로 또는 키).

        Returns:
            bytes: 파일 내용.

        Raises:
            FileNotFoundError: 파일을 찾을 수 없을 때.
            Exception: 파일 읽기 중 오류 발생 시.
        """
        ...

    def delete_file(self, identifier: str) -> bool:
        """
        주어진 식별자를 사용하여 파일을 삭제합니다.

        Args:
            identifier: 파일 식별자 (경로 또는 키).

        Returns:
            bool: 삭제 성공 여부.
        """
        ...


class LocalStorageHandler:
    """로컬 파일 시스템 저장소 핸들러"""
    def __init__(self, config: Config):
        self.config = config
        self.storage_path = config.LOCAL_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)

    def save_file(self, file: UploadFile) -> Tuple[str, str]:
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_id = str(uuid.uuid4())
        filename_base = unique_id
        filename = f"{filename_base}{file_extension}"
        file_path = os.path.join(self.storage_path, filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"파일 로컬 저장 완료: {file_path}")
            # file.file.seek(0) # 파일 포인터 원위치 (main.py에서 이미 처리)
            return file_path, file.filename
        except Exception as e:
            logger.error(f"로컬 파일 저장 실패 ({file_path}): {e}", exc_info=True)
            # 특정 오류 유형을 발생시키거나 None 반환 등 처리 방식 정의 필요
            raise Exception(f"로컬 파일 저장 실패: {e}")

    def read_file(self, identifier: str) -> bytes:
        file_path = identifier # 로컬에서는 식별자가 곧 파일 경로
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            logger.debug(f"로컬 파일 로드 완료: {file_path}")
            return content
        except FileNotFoundError:
            logger.error(f"로컬 파일을 찾을 수 없습니다: {file_path}")
            raise FileNotFoundError(f"로컬 파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            logger.error(f"로컬 파일 읽기 실패 ({file_path}): {e}", exc_info=True)
            raise Exception(f"로컬 파일 읽기 실패: {e}")

    def delete_file(self, identifier: str) -> bool:
        file_path = identifier
        try:
            os.remove(file_path)
            logger.debug(f"로컬 임시 파일 삭제 완료: {file_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"삭제할 로컬 파일 없음: {file_path}")
            return False # 파일이 없어도 실패는 아님
        except OSError as e:
            logger.warning(f"로컬 임시 파일 삭제 실패 ({file_path}): {e}")
            return False


class S3StorageHandler:
    """AWS S3 저장소 핸들러"""
    def __init__(self, config: Config):
        self.config = config
        if not config.S3_BUCKET:
            raise ValueError("S3 저장소 사용 설정되었으나 S3_BUCKET 설정값이 없습니다.")
        self.s3_bucket = config.S3_BUCKET
        self.s3_region = config.S3_REGION
        # boto3 클라이언트는 메서드 호출 시 생성하거나, 초기화 시 생성 가능
        # 여기서는 메서드 호출 시 생성하는 방식으로 구현
        # self.s3 = boto3.client('s3', region_name=self.s3_region)

    def _get_s3_client(self):
        # 실제 사용 시에는 AWS 자격증명 관리 방안 고려 필요
        # (예: 환경 변수, IAM 역할 등)
        return boto3.client('s3', region_name=self.s3_region)

    def save_file(self, file: UploadFile) -> Tuple[str, str]:
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_id = str(uuid.uuid4())
        # S3 Key 생성 (예: 'uploads/' 폴더 사용)
        s3_key = f"uploads/{unique_id}{file_extension}"

        try:
            s3 = self._get_s3_client()
            # 파일 포인터를 시작으로 이동 (중요!)
            file.file.seek(0)
            s3.upload_fileobj(
                file.file,
                self.s3_bucket,
                s3_key
            )
            logger.info(f"파일 S3 업로드 완료: s3://{self.s3_bucket}/{s3_key}")
            return s3_key, file.filename
        except ClientError as e:
            logger.error(f"S3 업로드 실패 (s3://{self.s3_bucket}/{s3_key}): {e}", exc_info=True)
            raise Exception(f"S3 업로드 실패: {e}")
        except Exception as e:
            logger.error(f"S3 처리 중 예상치 못한 오류 ({s3_key}): {e}", exc_info=True)
            raise Exception(f"S3 처리 중 오류 발생: {e}")

    def read_file(self, identifier: str) -> bytes:
        s3_key = identifier # S3에서는 식별자가 S3 키
        try:
            s3 = self._get_s3_client()
            s3_object = s3.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = s3_object['Body'].read()
            logger.debug(f"S3 파일 다운로드 완료: s3://{self.s3_bucket}/{s3_key}")
            return content
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                 logger.error(f"S3 파일을 찾을 수 없습니다: s3://{self.s3_bucket}/{s3_key}")
                 raise FileNotFoundError(f"S3 파일을 찾을 수 없습니다: s3://{self.s3_bucket}/{s3_key}")
            else:
                 logger.error(f"S3 파일 다운로드 실패 (s3://{self.s3_bucket}/{s3_key}): {e}", exc_info=True)
                 raise Exception(f"S3 파일 다운로드 실패: {e}")
        except Exception as e:
            logger.error(f"S3 처리 중 예상치 못한 오류 ({s3_key}): {e}", exc_info=True)
            raise Exception(f"S3 처리 중 오류 발생: {e}")

    def delete_file(self, identifier: str) -> bool:
        s3_key = identifier
        try:
            s3 = self._get_s3_client()
            s3.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            logger.debug(f"S3 객체 삭제 완료: s3://{self.s3_bucket}/{s3_key}")
            return True
        except ClientError as e:
            logger.warning(f"S3 객체 삭제 실패 (s3://{self.s3_bucket}/{s3_key}): {e}")
            return False
        except Exception as e:
            logger.error(f"S3 삭제 처리 중 예상치 못한 오류 ({s3_key}): {e}", exc_info=True)
            return False


# --- 팩토리 함수 ---

def get_storage_handler(config: Config) -> StorageHandler:
    """설정에 맞는 StorageHandler 인스턴스를 반환합니다."""
    storage_type = config.STORAGE_TYPE
    logger.info(f"저장소 타입: {storage_type}")

    if storage_type == "local":
        return LocalStorageHandler(config)
    elif storage_type == "s3":
        return S3StorageHandler(config)
    else:
        logger.error(f"지원하지 않는 저장소 타입입니다: {storage_type}")
        raise ValueError(f"지원하지 않는 저장소 타입입니다: {storage_type}") 