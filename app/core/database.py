from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from app.core.logger import get_logger

logger = get_logger("core.database")

# DATABASE_URL 환경 변수에서 읽어오기 (예: postgresql+asyncpg://user:pass@host:port/db)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db") # 기본값으로 로컬 SQLite 사용

logger.info(f"데이터베이스 연결 시도: {DATABASE_URL.split('@')[-1]}") # 로그에는 민감 정보 제외

engine = create_async_engine(DATABASE_URL, echo=bool(os.getenv("DB_ECHO", False)), future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입을 위한 DB 세션 생성기"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() # 기본적으로 commit 시도 (필요 없으면 제거)
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# TODO: 초기 테이블 생성이 필요하면 아래 함수 사용 (Alembic 권장)
# from app.models.base import Base
# async def init_db():
#     async with engine.begin() as conn:
#         # await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all) 