from fastapi import APIRouter

# Import endpoint routers using app path (reverted from src)
from app.api.v1.router.documents import router as documents_router
from app.api.v1.router.search import router as search_router
from app.api.v1.router.chat import router as chat_router

api_router = APIRouter()

# Include endpoint routers here
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
# api_router.include_router(rag.router, prefix="/rag", tags=["rag"]) # rag 엔드포인트가 있다면 추가 