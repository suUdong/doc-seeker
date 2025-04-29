# Service/Utility for processing documents (Parsing, Chunking)
import os
import io
from typing import List, Dict, Any, Optional
import pypdf # Use pypdf instead of PyPDF2 if applicable

# Import from app core locations
from app.core.config import AppConfig # Corrected path
from app.core.logger import get_logger

logger = get_logger("application.document_processor") # Updated logger name

class DocumentProcessor:
    """문서 처리 클래스 (서비스 계층 또는 유틸리티)"""
    
    # Removed config injection from __init__, pass values directly or get from config where needed
    # Or keep config injection if this will be a managed dependency
    # def __init__(self, config: AppConfig):
    #     self.config = config
    #     self.chunk_size = config.DOCUMENT_CHUNK_SIZE
    #     self.chunk_overlap = config.DOCUMENT_CHUNK_OVERLAP

    def process(self, filename: str, file_content: bytes, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
        """
        파일 내용을 처리하여 청크로 분할
        
        Args:
            filename: 파일 이름
            file_content: 파일 내용 (바이트)
            chunk_size: 청크 크기
            chunk_overlap: 청크 중첩 크기
            
        Returns:
            List[Dict]: 청크 목록 ({'text': str, 'source': str, 'page': Optional[int]})
        """
        try:
            file_extension = os.path.splitext(filename)[1].lower()
            logger.debug(f"파일 처리 시작: {filename} (Type: {file_extension})")

            if file_extension == '.pdf':
                return self._process_pdf(filename, file_content, chunk_size, chunk_overlap)
            elif file_extension in ['.txt', '.md']: # Add other text formats if needed
                return self._process_text(filename, file_content, chunk_size, chunk_overlap)
            else:
                logger.warning(f"지원되지 않는 파일 형식 건너뛰기: {filename}")
                return []
                
        except Exception as e:
            logger.exception(f"문서 처리 중 오류 ({filename}): {e}")
            return [] # Return empty list on error
    
    def _process_pdf(self, filename: str, file_content: bytes, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
        """PDF 파일 처리"""
        chunks = []
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            logger.info(f"PDF 페이지 수: {len(pdf_reader.pages)} ({filename}) ")

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if not text or text.isspace():
                        logger.debug(f"빈 페이지 건너뛰기: {filename}, Page {page_num + 1}")
                        continue
                    
                    page_chunks = self._split_text(text, chunk_size, chunk_overlap)
                    
                    for chunk_text in page_chunks:
                        chunks.append({
                            "text": chunk_text,
                            "source": filename,
                            "page": page_num + 1
                        })
                except Exception as page_err:
                     logger.error(f"PDF 페이지 처리 오류 ({filename}, Page {page_num + 1}): {page_err}")
                     continue # Skip problematic pages
            
            logger.info(f"PDF 처리 완료: {filename}, {len(chunks)} 청크 생성")
            
        except pypdf.errors.PdfReadError as pdf_err:
             logger.error(f"PDF 파일 읽기 오류 ({filename}): {pdf_err} - 파일이 손상되었거나 암호화되었을 수 있습니다.")
        except Exception as e:
            logger.exception(f"PDF 처리 중 예상치 못한 오류 ({filename}): {e}")
            
        return chunks
    
    def _process_text(self, filename: str, file_content: bytes, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
        """텍스트 파일 처리"""
        chunks = []
        try:
            text = None
            # Common encodings to try
            encodings = ['utf-8', 'euc-kr', 'cp949', 'latin-1'] 
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    logger.info(f"텍스트 파일 디코딩 성공 ({filename}, Encoding: {encoding})")
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                logger.warning(f"모든 인코딩 시도 실패, 텍스트 디코딩 불가: {filename}")
                return []
            
            text_chunks = self._split_text(text, chunk_size, chunk_overlap)
            
            for chunk_text in text_chunks:
                chunks.append({
                    "text": chunk_text,
                    "source": filename,
                    "page": None # Text files don't have pages
                })
            
            logger.info(f"텍스트 파일 처리 완료: {filename}, {len(chunks)} 청크 생성")
            
        except Exception as e:
            logger.exception(f"텍스트 파일 처리 중 오류 ({filename}): {e}")
            
        return chunks
    
    def _split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """텍스트를 재귀적으로 분할 (LangChain 방식 유사)"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Use a robust text splitter like RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False, # Use default separators
            separators=["\n\n", "\n", ".", " ", ""] # Common separators
        )
        
        try:
            split_chunks = text_splitter.split_text(text)
            logger.debug(f"텍스트 분할: {len(split_chunks)} 청크 생성 (Size: {chunk_size}, Overlap: {chunk_overlap})")
            # Filter out empty or whitespace-only chunks that might be generated
            return [chunk for chunk in split_chunks if chunk and not chunk.isspace()]
        except Exception as e:
            logger.exception(f"텍스트 분할 중 오류: {e}")
            # Fallback: return the original text as a single chunk if splitting fails
            return [text] if text and not text.isspace() else []

# If this class is intended to be used as a singleton dependency:
# def get_document_processor(config: AppConfig = Depends(get_app_config)) -> DocumentProcessor:
#    return DocumentProcessor(config) 