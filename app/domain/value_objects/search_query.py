from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)  # 불변(immutable) 값 객체
class SearchQuery:
    """검색 쿼리 값 객체
    
    사용자가 입력한 검색 쿼리를 나타내는 값 객체입니다.
    """
    text: str  # 쿼리 텍스트
    top_k: int = 5  # 검색 결과 개수 제한
    
    def __post_init__(self):
        """데이터 유효성 검증"""
        if not self.text or self.text.isspace():
            raise ValueError("검색 쿼리는 비어있거나 공백만으로 구성될 수 없습니다.")
        
        if self.top_k < 1:
            raise ValueError("top_k는 1 이상이어야 합니다.") 