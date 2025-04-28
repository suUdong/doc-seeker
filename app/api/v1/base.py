from fastapi import APIRouter

# Import endpoint routers here after they are created
from .endpoints import documents, search #, rag

api_router = APIRouter()

# Include endpoint routers here
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
# api_router.include_router(rag.router, prefix="/rag", tags=["rag"]) 