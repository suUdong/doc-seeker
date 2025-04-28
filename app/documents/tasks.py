# Background tasks for document processing 
import logging
from app.config import AppConfig
from app.rag.rag_service import RAGService
# Import the concrete implementation function directly for background task
from app.core.storage import StorageHandler, get_storage_handler as get_storage_handler_impl
from app.logger import get_logger

logger = get_logger("tasks.documents")

async def process_document_indexing(
    identifier: str,
    original_filename: str,
    storage_type: str,
    rag_service: RAGService, # Passed from the route
    config: AppConfig,       # Passed from the route
):
    """문서 인덱싱을 처리하는 백그라운드 작업"""
    logger.info(f"'{original_filename}' 문서 인덱싱 시작 (Identifier: {identifier}, Storage: {storage_type}).")
    # Background tasks cannot use Depends(), so we get the handler implementation directly
    storage_handler: StorageHandler = get_storage_handler_impl(config)

    try:
        # Read file using the storage handler
        # Assuming storage handler methods are async
        file_content = await storage_handler.read_file(identifier)
        if not file_content:
            logger.error(f"저장소에서 파일을 읽지 못했습니다: {identifier}")
            return

        logger.info(f"'{original_filename}' 파일 내용 로드 완료.")

        # Use file_content (bytes) directly with RAGService
        # Assuming index_document is async
        success = await rag_service.index_document(file_content, original_filename)

        if success:
            logger.info(f"'{original_filename}' 문서 인덱싱 성공.")
        else:
            logger.error(f"'{original_filename}' 문서 인덱싱 실패.")

    except FileNotFoundError:
        logger.error(f"인덱싱 처리 중 파일을 찾을 수 없습니다: {identifier}")
    except Exception as e:
        logger.exception(f"'{original_filename}' 문서 인덱싱 중 오류 발생: {e}")
    finally:
        # Attempt to delete the file after processing
        try:
            logger.info(f"처리 후 파일 삭제 시도: {identifier}")
            # Assuming delete_file is async
            await storage_handler.delete_file(identifier)
            logger.info(f"파일 삭제 완료: {identifier}")
        except FileNotFoundError:
            logger.warning(f"삭제할 파일을 찾을 수 없습니다 (이미 삭제되었거나 읽기 실패했을 수 있음): {identifier}")
        except Exception as e:
            logger.exception(f"파일 삭제 중 오류 발생 {identifier}: {e}") 