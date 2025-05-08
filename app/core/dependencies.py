# FastAPI dependency functions 
from functools import lru_cache
from fastapi import Depends
import logging
from qdrant_client import QdrantClient
from typing import Optional

# Core components
from app.core.config import AppConfig
from app.infrastructure.storage.storage import StorageHandler, get_storage_handler as get_storage_handler_from_infra
from app.core.logger import get_logger
from app.core.database import get_db, AsyncSession

# Domain repositories & services
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.chunk_repository import ChunkRepository
from app.domain.services.document_processing_service import DocumentProcessingService
from app.domain.services.llm_service import LLMService
from app.domain.services.rag_service import RAGService
from app.domain.services.storage_service import StorageService

# Infrastructure implementations
from app.infrastructure.repository.memory_document_repository import InMemoryDocumentRepository
from app.infrastructure.repository.qdrant_chunk_repository import QdrantChunkRepository
from app.infrastructure.document.document_processing_service_impl import DocumentProcessingServiceImpl
from app.infrastructure.embedding.embedding_service import EmbeddingService, SentenceTransformerEmbedding
from app.infrastructure.llm.llama_service import LlamaService
from app.infrastructure.rag.llama_rag_service import LlamaRAGService
from app.infrastructure.storage.storage_factory import get_storage_service as get_storage_service_from_factory

# Application use cases
from app.application.use_cases.upload_document import UploadDocumentUseCase
from app.application.use_cases.index_document import IndexDocumentUseCase
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.application.use_cases.chat import ChatUseCase

# Legacy services (removed)
# from app.application.use_cases.model_manager import ModelManager
# from app.application.use_cases.rag_service import RAGService

logger = get_logger("core.dependencies")

# --- Core Dependencies ---

@lru_cache()
def get_app_config() -> AppConfig:
    """
    애플리케이션 설정을 가져옵니다.
    환경 변수와 프로필 설정에 따라 적절한 설정이 로드됩니다.
    결과는 캐시되어 반복 호출 시 성능을 향상시킵니다.
    """
    try:
        return AppConfig()
    except Exception as e:
        logger.exception("설정 로드 실패!")
        raise RuntimeError("애플리케이션 설정을 로드할 수 없습니다") from e

def get_storage_handler(
    config: AppConfig = Depends(get_app_config)
) -> StorageHandler:
    """스토리지 핸들러 제공"""
    logger.debug(f"스토리지 핸들러 제공: 유형={config.STORAGE_TYPE}")
    return get_storage_handler_from_infra(config)

def get_storage_service(
    config: AppConfig = Depends(get_app_config)
) -> StorageService:
    """저장소 서비스 제공"""
    logger.debug(f"저장소 서비스 제공: 유형={config.STORAGE_TYPE}")
    return get_storage_service_from_factory(config)

# --- Infrastructure Dependencies ---

@lru_cache()
def get_qdrant_client(
    config: AppConfig = Depends(get_app_config)
) -> QdrantClient:
    """Qdrant 클라이언트 제공"""
    try:
        logger.info(f"Qdrant 클라이언트 초기화: {config.QDRANT_HOST}:{config.QDRANT_PORT}")
        return QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    except Exception as e:
        logger.exception("Qdrant 클라이언트 초기화 실패!")
        raise RuntimeError("Qdrant 클라이언트를 초기화할 수 없습니다") from e

@lru_cache()
def get_embedding_service(
    config: AppConfig = Depends(get_app_config)
) -> EmbeddingService:
    """임베딩 서비스 제공"""
    try:
        logger.info(f"임베딩 서비스 초기화: 모델={config.EMBEDDING_MODEL_ID}")
        return SentenceTransformerEmbedding(config=config)
    except Exception as e:
        logger.exception("임베딩 서비스 초기화 실패!")
        raise RuntimeError("임베딩 서비스를 초기화할 수 없습니다") from e

# --- Repository Dependencies ---

@lru_cache()
def get_document_repository() -> DocumentRepository:
    """문서 저장소 제공 (현재는 메모리 기반)"""
    try:
        logger.info("메모리 기반 문서 저장소 초기화")
        return InMemoryDocumentRepository()
    except Exception as e:
        logger.exception("문서 저장소 초기화 실패!")
        raise RuntimeError("문서 저장소를 초기화할 수 없습니다") from e

@lru_cache()
def get_chunk_repository(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    config: AppConfig = Depends(get_app_config)
) -> ChunkRepository:
    """청크 저장소 제공 (Qdrant 기반)"""
    try:
        logger.info(f"Qdrant 기반 청크 저장소 초기화: 콜렉션={config.QDRANT_COLLECTION_NAME}")
        return QdrantChunkRepository(
            client=qdrant_client,
            embedding_service=embedding_service,
            config=config
        )
    except Exception as e:
        logger.exception("청크 저장소 초기화 실패!")
        raise RuntimeError("청크 저장소를 초기화할 수 없습니다") from e

# --- Domain Service Dependencies ---

@lru_cache()
def get_document_processing_service() -> DocumentProcessingService:
    """문서 처리 서비스 제공"""
    try:
        logger.info("문서 처리 서비스 초기화")
        return DocumentProcessingServiceImpl()
    except Exception as e:
        logger.exception("문서 처리 서비스 초기화 실패!")
        raise RuntimeError("문서 처리 서비스를 초기화할 수 없습니다") from e

@lru_cache()
def get_llm_service(
    config: AppConfig = Depends(get_app_config)
) -> LLMService:
    """LLM 서비스 제공"""
    try:
        logger.info("LLM 서비스 초기화")
        return LlamaService(config=config)
    except Exception as e:
        logger.exception("LLM 서비스 초기화 실패!")
        raise RuntimeError("LLM 서비스를 초기화할 수 없습니다") from e

@lru_cache()
def get_rag_service(
    llm_service: LLMService = Depends(get_llm_service),
    config: AppConfig = Depends(get_app_config)
) -> RAGService:
    """RAG 서비스 제공"""
    try:
        logger.info("RAG 서비스 초기화")
        return LlamaRAGService(
            llm_service=llm_service,
            config=config
        )
    except Exception as e:
        logger.exception("RAG 서비스 초기화 실패!")
        raise RuntimeError("RAG 서비스를 초기화할 수 없습니다") from e

# --- Use Case Dependencies ---

def get_upload_document_use_case(
    document_repository: DocumentRepository = Depends(get_document_repository),
    storage_service: StorageService = Depends(get_storage_service)
) -> UploadDocumentUseCase:
    """문서 업로드 유스케이스 제공"""
    return UploadDocumentUseCase(
        document_repository=document_repository,
        storage_service=storage_service
    )

def get_index_document_use_case(
    document_repository: DocumentRepository = Depends(get_document_repository),
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
    document_processing_service: DocumentProcessingService = Depends(get_document_processing_service),
    storage_service: StorageService = Depends(get_storage_service),
    config: AppConfig = Depends(get_app_config)
) -> IndexDocumentUseCase:
    """문서 인덱싱 유스케이스 제공"""
    return IndexDocumentUseCase(
        document_repository=document_repository,
        chunk_repository=chunk_repository,
        document_processing_service=document_processing_service,
        storage_service=storage_service,
        config=config
    )

def get_search_documents_use_case(
    chunk_repository: ChunkRepository = Depends(get_chunk_repository)
) -> SearchDocumentsUseCase:
    """문서 검색 유스케이스 제공"""
    return SearchDocumentsUseCase(
        chunk_repository=chunk_repository
    )

def get_chat_use_case(
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
    rag_service: RAGService = Depends(get_rag_service),
    config: AppConfig = Depends(get_app_config)
) -> ChatUseCase:
    """챗 유스케이스 제공"""
    return ChatUseCase(
        chunk_repository=chunk_repository,
        rag_service=rag_service,
        config=config
    )

# --- Legacy Dependencies (삭제) ---
# @lru_cache()
# def get_model_manager(config: AppConfig = Depends(get_app_config)) -> ModelManager:
#     """레거시 모델 매니저 제공"""
#     try:
#         return ModelManager(config=config)
#     except Exception as e:
#         logger.exception("ModelManager 초기화 실패!")
#         raise RuntimeError("ModelManager를 초기화할 수 없습니다") from e
# 
# @lru_cache()
# def get_rag_service(
#     config: AppConfig = Depends(get_app_config),
#     model_manager: ModelManager = Depends(get_model_manager)
# ) -> RAGService:
#     """레거시 RAG 서비스 제공"""
#     try:
#         return RAGService(config=config, model_manager=model_manager)
#     except Exception as e:
#         logger.exception("RAGService 초기화 실패!")
#         raise RuntimeError("RAGService를 초기화할 수 없습니다") from e

# DB Session dependency using the function from database.py
# This function itself can be used with Depends() directly in routers/services
# Or you can create an alias here if preferred
# async def get_db_session() -> AsyncSession:
#     async for session in get_db():
#         yield session

# Add other dependencies like DocumentProcessor if needed
# ... 

def get_storage_config(config: AppConfig = Depends(get_app_config)):
    """스토리지 관련 설정을 반환합니다."""
    return {
        "storage_type": config.STORAGE_TYPE,
        "local_storage_path": config.LOCAL_STORAGE_PATH,
        "s3_bucket": config.S3_BUCKET,
        "s3_region": config.S3_REGION
    }

def get_model_config(config: AppConfig = Depends(get_app_config)):
    """모델 관련 설정을 반환합니다."""
    return {
        "model_base_path": config.MODEL_BASE_PATH,
        "embedding_model_id": config.EMBEDDING_MODEL_ID,
        "embedding_batch_size": config.EMBEDDING_BATCH_SIZE,
        "generation_model_type": config.GENERATION_MODEL_TYPE,
        "generation_model_id": config.GENERATION_MODEL_ID,
        "generation_model_gguf_filename": config.GENERATION_MODEL_GGUF_FILENAME,
        "model_path": config.get_model_path(),
        "embedding_path": config.get_embedding_path()
    }

def get_generation_config(config: AppConfig = Depends(get_app_config)):
    """생성 모델 관련 설정을 반환합니다."""
    if config.GENERATION_MODEL_TYPE == "gguf":
        return {
            "gpu_layers": config.GPU_LAYERS,
            "context_length": config.CT_CONTEXT_LENGTH,
            "max_new_tokens": config.CT_MAX_NEW_TOKENS,
            "temperature": config.CT_TEMPERATURE,
            "top_p": config.CT_TOP_P
        }
    else:
        return {
            "max_answer_length": config.MAX_ANSWER_LENGTH,
            "temperature": config.GENERATION_TEMPERATURE,
            "top_p": config.GENERATION_TOP_P
        }

def get_qdrant_config(config: AppConfig = Depends(get_app_config)):
    """Qdrant 관련 설정을 반환합니다."""
    return {
        "host": config.QDRANT_HOST,
        "port": config.QDRANT_PORT,
        "collection_name": config.QDRANT_COLLECTION_NAME,
        "score_threshold": config.QDRANT_SCORE_THRESHOLD
    }

def get_environment_info(config: AppConfig = Depends(get_app_config)):
    """현재 실행 환경 정보를 반환합니다."""
    return {
        "environment": config.ENVIRONMENT,
        "env_profile": config.ENV_PROFILE,
        "debug": config.DEBUG
    } 