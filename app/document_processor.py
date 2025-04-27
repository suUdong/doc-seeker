import os
import io
from typing import List, Dict, Any, Optional
import pypdf
from app.logger import get_logger

logger = get_logger("document_processor")

class DocumentProcessor:
    """문서 처리 클래스"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        DocumentProcessor 초기화
        
        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 중복 크기 (문자 수)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process(self, filename: str, file_content: bytes) -> List[Dict[str, Any]]:
        """
        파일 내용을 처리하여 청크로 분할
        
        Args:
            filename: 파일 이름
            file_content: 파일 내용 (바이트)
            
        Returns:
            List[Dict]: 청크 목록
        """
        try:
            file_extension = os.path.splitext(filename)[1].lower()
            
            # 파일 유형에 따라 적절한 처리 함수 호출
            if file_extension == '.pdf':
                return self._process_pdf(filename, file_content)
            elif file_extension in ['.txt', '.md']:
                return self._process_text(filename, file_content)
            else:
                logger.warning(f"지원되지 않는 파일 형식: {file_extension}")
                return []
                
        except Exception as e:
            logger.error(f"문서 처리 오류: {str(e)}")
            return []
    
    def _process_pdf(self, filename: str, file_content: bytes) -> List[Dict[str, Any]]:
        """PDF 파일 처리"""
        chunks = []
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                
                if not text or text.isspace():
                    continue
                
                # 페이지 텍스트를 청크로 분할
                page_chunks = self._split_text(text)
                
                for chunk in page_chunks:
                    chunks.append({
                        "text": chunk,
                        "source": filename,
                        "page": page_num + 1
                    })
            
            logger.info(f"PDF 처리 완료: {filename}, {len(chunks)} 청크 생성")
            
        except Exception as e:
            logger.error(f"PDF 처리 오류: {str(e)}")
            
        return chunks
    
    def _process_text(self, filename: str, file_content: bytes) -> List[Dict[str, Any]]:
        """텍스트 파일 처리"""
        chunks = []
        
        try:
            # 텍스트 디코딩 시도 (인코딩 자동 감지)
            encodings = ['utf-8', 'euc-kr', 'cp949']
            text = None
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                logger.warning(f"텍스트 디코딩 실패: {filename}")
                return []
            
            # 텍스트를 청크로 분할
            text_chunks = self._split_text(text)
            
            for chunk in text_chunks:
                chunks.append({
                    "text": chunk,
                    "source": filename,
                    "page": 1  # 텍스트 파일은 페이지 개념이 없음
                })
            
            logger.info(f"텍스트 파일 처리 완료: {filename}, {len(chunks)} 청크 생성")
            
        except Exception as e:
            logger.error(f"텍스트 파일 처리 오류: {str(e)}")
            
        return chunks
    
    def _split_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 원본 텍스트
            
        Returns:
            List[str]: 청크 목록
        """
        chunks = []
        
        if not text:
            return chunks
        
        # 먼저 단락으로 분할
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 불필요한 공백 제거
            paragraph = paragraph.strip()
            
            if not paragraph:
                continue
            
            # 현재 청크에 단락을 추가했을 때 청크 크기를 초과하는지 확인
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                # 현재 청크가 이미 있으면 추가
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 단락이 청크 크기보다 큰 경우 강제 분할
                if len(paragraph) > self.chunk_size:
                    # 문장 단위로 분할
                    sentences = paragraph.replace('. ', '.\n').split('\n')
                    
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > self.chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk)
                            
                            # 문장이 청크 크기보다 큰 경우 한 번에 추가
                            if len(sentence) > self.chunk_size:
                                chunks.append(sentence[:self.chunk_size])
                            else:
                                current_chunk = sentence
                        else:
                            if current_chunk:
                                current_chunk += " " + sentence
                            else:
                                current_chunk = sentence
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        # 청크 중복 설정
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            
            for i in range(len(chunks)):
                if i == 0:
                    overlapped_chunks.append(chunks[i])
                else:
                    # 이전 청크의 끝부분을 현재 청크의 시작부분에 추가
                    prev_chunk = chunks[i-1]
                    current_chunk = chunks[i]
                    
                    overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                    
                    overlapped_chunks.append(overlap_text + current_chunk)
            
            chunks = overlapped_chunks
        
        return chunks 