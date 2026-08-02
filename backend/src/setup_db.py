"""
setup_db.py
统一的数据库初始化与结构同步脚本（最新版）

功能：
1. 自动创建所有数据库表（如果不存在）
2. 自动同步/同步最新字段（兼容旧表结构）
3. 初始化默认用户数据
4. 自动创建索引
"""

import asyncio
import io
import sys

# Windows 下强制标准输出为 UTF-8，避免 emoji / 中文打印触发 UnicodeEncodeError
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from sqlalchemy import text
from db.database import engine, AsyncSessionLocal
from db.models import Base
from config import DB_IS_SQLITE


async def get_table_columns(db, table: str) -> set:
    """按数据库方言获取表的所有列名"""
    if DB_IS_SQLITE:
        result = await db.execute(text(f"PRAGMA table_info({table})"))
        return {row[1] for row in result.fetchall()}
    result = await db.execute(text(f"DESCRIBE {table}"))
    return {row[0] for row in result.fetchall()}


async def setup_database():
    """初始化/同步数据库"""
    print("\n" + "=" * 60)
    print(" 🌸 Sakura 数据库初始化与同步")
    print("=" * 60)
    
    try:
        # 1. 创建所有表（如果不存在）
        print("\n[1/4] 检查并创建数据库表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✅ 核心表结构检查完成")
        
        # 2. 结构同步（确保字段是最新的）
        print("\n[2/4] 同步字段结构（支持平滑升级）...")
        async with AsyncSessionLocal() as db:
            # --- conversations 表 ---
            columns = await get_table_columns(db, "conversations")
            
            if "vector_id" not in columns:
                await db.execute(text(
                    "ALTER TABLE conversations ADD COLUMN vector_id VARCHAR(100) DEFAULT ''"
                    + ("" if DB_IS_SQLITE else " AFTER timestamp")
                ))
                print("  ✅ 添加 conversations.vector_id")
            if "emotion_type" not in columns:
                await db.execute(text(
                    "ALTER TABLE conversations ADD COLUMN emotion_type VARCHAR(20) DEFAULT 'calm'"
                    + ("" if DB_IS_SQLITE else " AFTER vector_id")
                ))
                print("  ✅ 添加 conversations.emotion_type")
            if "importance" not in columns:
                await db.execute(text(
                    "ALTER TABLE conversations ADD COLUMN importance INT DEFAULT 3"
                    + ("" if DB_IS_SQLITE else " AFTER emotion_type")
                ))
                print("  ✅ 添加 conversations.importance")
                
            # --- long_term_memory 表 ---
            ltm_columns = await get_table_columns(db, "long_term_memory")
            if "vector_id" not in ltm_columns:
                await db.execute(text(
                    "ALTER TABLE long_term_memory ADD COLUMN vector_id VARCHAR(100) DEFAULT ''"
                    + ("" if DB_IS_SQLITE else " AFTER updated_at")
                ))
                print("  ✅ 添加 long_term_memory.vector_id")

            # --- 角色转换修复 ---
            await db.execute(text("UPDATE conversations SET role = 'sakura' WHERE role = 'assistant'"))
            
            await db.commit()
        
        # 3. 初始化默认数据
        print("\n[3/4] 初始化默认用户状态...")
        async with AsyncSessionLocal() as db:
            _insert_prefix = "INSERT OR IGNORE INTO" if DB_IS_SQLITE else "INSERT INTO"
            _upsert_suffix = (
                ""
                if DB_IS_SQLITE
                else " ON DUPLICATE KEY UPDATE user_id=user_id"
            )
            await db.execute(text(
                f"{_insert_prefix} user_states "
                "(user_id, affinity, mood, emotion_type, energy_level, emotion_updated_at, last_interaction, total_messages) "
                "VALUES ('default_user', 0, 50, 'calm', 80, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)"
                + _upsert_suffix
            ))
            await db.commit()
        print("  ✅ 默认用户状态就绪")
        
        # 4. 索引优化
        print("\n[4/4] 检查并优化索引...")
        async with AsyncSessionLocal() as db:
            indices = [
                ("idx_vector_id", "conversations", "vector_id"),
                ("idx_importance", "conversations", "importance"),
                ("idx_ltm_vector_id", "long_term_memory", "vector_id"),
            ]
            for idx_name, table, col in indices:
                try:
                    await db.execute(text(f"CREATE INDEX {idx_name} ON {table}({col})"))
                    print(f"  ✅ 创建索引 {table}.{idx_name}")
                except Exception as e:
                    msg = str(e).lower()
                    # 索引已存在（MySQL / SQLite 提示不同）
                    if "already exists" in msg or "duplicate key name" in msg:
                        pass
            await db.commit()

        print("\n" + "=" * 60)
        print(" ✅ 数据库设置完成！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(setup_database())
