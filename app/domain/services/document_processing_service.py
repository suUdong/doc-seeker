from typing import List, Dict, Any, Optional
import os
import io
from datetime import datetime
from abc import ABC, abstractmethod

# 값 객체 및 엔티티 임포트
from app.domain.value_objects.document_chunk import DocumentChunk
from app.domain.entities.document import DocumentEntity

class DocumentProcessingService(ABC):
    """문서 처리 도메인 서비스
    
    문서 청킹 및 텍스트 추출과 같은 문서 처리 관련 핵심 로직을 포함합니다.
    이 서비스는 특정 외부 라이브러리에 의존하지 않도록 인터페이스만 정의합니다.
    """
    
    @abstractmethod
    def extract_text_from_pdf(self, file_content: bytes) -> Dict[int, str]:
        """PDF 파일에서 텍스트 추출 (인터페이스)
        
        Args:
            file_content: PDF 파일 내용
            
        Returns:
            Dict[int, str]: 페이지 번호를 키로, 추출된 텍스트를 값으로 하는 사전
        """
        # 실제 구현은 인프라스트럭처 계층에 위임
        # 이는 인터페이스만 정의하는 부분
        pass
    
    @abstractmethod
    def extract_text_from_text_file(self, file_content: bytes) -> str:
        """텍스트 파일에서 텍스트 추출 (인터페이스)
        
        Args:
            file_content: 텍스트 파일 내용
            
        Returns:
            str: 추출된 텍스트
        """
        # 실제 구현은 인프라스트럭처 계층에 위임
        pass
    
    @abstractmethod
    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """텍스트를 청크로 분할 (인터페이스)
        
        Args:
            text: 분할할 텍스트
            chunk_size: 청크 크기
            chunk_overlap: 청크 중첩 크기
            
        Returns:
            List[str]: 분할된 청크 텍스트 목록
        """
        # 실제 구현은 인프라스트럭처 계층에 위임
        pass
    
    @abstractmethod
    def create_document_chunks(self, 
                               document_id: str, 
                               filename: str, 
                               file_content: bytes, 
                               chunk_size: int, 
                               chunk_overlap: int) -> List[DocumentChunk]:
        """파일에서 문서 청크 생성 (인터페이스)
        
        Args:
            document_id: 문서 ID
            filename: 파일명
            file_content: 파일 내용
            chunk_size: 청크 크기
            chunk_overlap: 청크 중첩 크기
            
        Returns:
            List[DocumentChunk]: 생성된 청크 목록
        """
        # 실제 구현은 인프라스트럭처 계층에 위임
        pass 