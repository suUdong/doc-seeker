from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    """대화 메시지 모델"""
    role: str = Field(..., description="메시지 역할 (user/assistant)")
    content: str = Field(..., description="메시지 내용")

class ChatRequest(BaseModel):
    """챗 요청 모델"""
    message: str = Field(..., description="사용자 메시지")
    history: Optional[List[ChatMessage]] = Field(default=None, description="이전 대화 내역 (선택)")
    limit: Optional[int] = Field(default=5, description="검색할 문서 수 (선택)")

class SourceDocument(BaseModel):
    """소스 문서 모델"""
    text: str = Field(..., description="문서 텍스트")
    document_id: str = Field(..., description="문서 ID")
    page_number: Optional[str] = Field(default=None, description="페이지 번호 (선택)")
    score: Optional[float] = Field(default=None, description="검색 점수 (선택)")

class ChatResponse(BaseModel):
    """챗 응답 모델"""
    message: str = Field(..., description="생성된 응답 메시지")
    sources: List[SourceDocument] = Field(default_factory=list, description="참조 소스 문서 목록") 