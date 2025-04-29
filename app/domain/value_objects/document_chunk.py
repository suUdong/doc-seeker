from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)  # 불변(immutable) 값 객체
class DocumentChunk:
    """문서 청크 값 객체
    
    문서의 내용을 나타내는 작은 조각(청크)으로, 검색 및 인덱싱에 사용됩니다.
    값 객체이므로 고유 식별자를 가지지 않고, 내용 자체가 식별자 역할을 합니다.
    """
    text: str  # 청크 텍스트 내용
    source: str  # 원본 문서 파일명
    document_id: str  # 원본 문서 ID
    page: Optional[int] = None  # 페이지 번호 (PDF 등)
    index: Optional[int] = None  # 문서 내 인덱스 위치
    
    def __post_init__(self):
        """데이터 유효성 검증"""
        if not self.text or self.text.isspace():
            raise ValueError("청크 텍스트는 비어있거나 공백만으로 구성될 수 없습니다.") 