from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
from config import DATABASE_URL, DB_IS_SQLITE
from db.models import Base

# SQLite 不适用连接池参数（MySQL 使用连接池）
_engine_kwargs = {"echo": False}
if not DB_IS_SQLITE:
    _engine_kwargs.update(pool_size=5, max_overflow=10)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    **_engine_kwargs
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """获取数据库会话（依赖注入用）"""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_session():
    """获取数据库会话（用于 async with 的上下文管理器）"""
    async with AsyncSessionLocal() as session:
        yield session
