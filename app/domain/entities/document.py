from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class DocumentEntity:
    """문서 도메인 엔티티"""
    id: str  # 문서 고유 식별자
    filename: str  # 원본 파일명
    upload_date: datetime  # 업로드 일시
    metadata: Dict[str, Any] = None  # 메타데이터 (페이지 수, 크기 등)
    indexed: bool = False  # 인덱싱 완료 여부
    
    def mark_as_indexed(self):
        """문서 인덱싱 완료 표시"""
        self.indexed = True
        
    def update_metadata(self, metadata: Dict[str, Any]):
        """메타데이터 업데이트"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update(metadata) 