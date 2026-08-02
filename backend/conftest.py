"""pytest 全局配置：测试默认使用独立的 SQLite 数据库，避免依赖 MySQL。"""

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_TEST_DB = _ROOT / "src" / "db" / "data" / "test_sakura.db"

# 必须在任何业务模块 import 之前设置，config.py 会优先保留已有环境变量
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{_TEST_DB.as_posix()}",
)

import pytest


def _remove_test_db_files():
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(_TEST_DB) + suffix)
        try:
            p.unlink(missing_ok=True)
        except PermissionError:
            pass


@pytest.fixture(scope="session", autouse=True)
def reset_test_db():
    """会话开始/结束时清理测试数据库文件"""
    _remove_test_db_files()
    yield
    # 先释放数据库连接，再清理文件
    try:
        import asyncio
        from db.database import engine
        asyncio.run(engine.dispose())
    except Exception:
        pass
    _remove_test_db_files()


@pytest.fixture(scope="session", autouse=True)
def ensure_db_tables(reset_test_db):
    """确保所有表已创建（等价于运行 setup_db.py 的第一步）"""
    import asyncio
    from db.database import init_db
    asyncio.run(init_db())
