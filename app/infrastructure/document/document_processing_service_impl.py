from typing import List, Dict, Any, Optional
import os
import io
import pypdf  # pypdf 사용
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.domain.value_objects.document_chunk import DocumentChunk
from app.domain.services.document_processing_service import DocumentProcessingService
from app.core.logger import get_logger

logger = get_logger("infrastructure.document.processing")

class DocumentProcessingServiceImpl(DocumentProcessingService):
    """문서 처리 서비스 구현체
    
    도메인 서비스 인터페이스의 실제 구현을 제공합니다.
    이 클래스는 실제 라이브러리(pypdf, langchain)에 의존합니다.
    """
    
    def extract_text_from_pdf(self, file_content: bytes) -> Dict[int, str]:
        """PDF 파일에서 텍스트 추출"""
        result = {}
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text and not text.isspace():
                        result[page_num + 1] = text  # 1-based 페이지 번호
                except Exception as e:
                    logger.error(f"PDF 페이지 처리 중 오류 (Page {page_num + 1}): {e}")
            
            logger.info(f"PDF 텍스트 추출 완료: {len(result)} 페이지")
        except Exception as e:
            logger.exception(f"PDF 텍스트 추출 중 오류: {e}")
        
        return result
    
    def extract_text_from_text_file(self, file_content: bytes) -> str:
        """텍스트 파일에서 텍스트 추출"""
        # 여러 인코딩 시도
        encodings = ['utf-8', 'euc-kr', 'cp949', 'latin-1']
        text = None
        
        for encoding in encodings:
            try:
                text = file_content.decode(encoding)
                logger.info(f"텍스트 파일 디코딩 성공 (Encoding: {encoding})")
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            logger.warning("텍스트 디코딩 실패: 모든 인코딩 시도 실패")
            return ""
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """텍스트를 청크로 분할"""
        if not text or text.isspace():
            return []
        
        # langchain RecursiveCharacterTextSplitter 사용
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        try:
            chunks = text_splitter.split_text(text)
            logger.debug(f"텍스트 분할 완료: {len(chunks)} 청크 생성")
            return [chunk for chunk in chunks if chunk and not chunk.isspace()]
        except Exception as e:
            logger.exception(f"텍스트 분할 중 오류: {e}")
            return [text] if text and not text.isspace() else []
    
    def create_document_chunks(self, 
                               document_id: str, 
                               filename: str, 
                               file_content: bytes, 
                               chunk_size: int, 
                               chunk_overlap: int) -> List[DocumentChunk]:
        """파일 내용에서 문서 청크 생성"""
        chunks = []
        extension = os.path.splitext(filename)[1].lower()
        
        if extension == '.pdf':
            # PDF 파일 처리
            page_texts = self.extract_text_from_pdf(file_content)
            
            for page_num, page_text in page_texts.items():
                text_chunks = self.chunk_text(page_text, chunk_size, chunk_overlap)
                
                for i, chunk_text in enumerate(text_chunks):
                    chunks.append(DocumentChunk(
                        text=chunk_text,
                        source=filename,
                        document_id=document_id,
                        page=page_num,
                        index=i
                    ))
        
        elif extension in ['.txt', '.md']:
            # 텍스트 파일 처리
            text = self.extract_text_from_text_file(file_content)
            text_chunks = self.chunk_text(text, chunk_size, chunk_overlap)
            
            for i, chunk_text in enumerate(text_chunks):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    source=filename,
                    document_id=document_id,
                    page=None,
                    index=i
                ))
        
        else:
            logger.warning(f"지원되지 않는 파일 형식: {extension}")
        
        logger.info(f"문서 청크 생성 완료: {filename}, {len(chunks)} 청크")
        return chunks 