"""
migrate_db.py
数据库表结构迁移脚本（一次性使用）。

变更内容：
  - long_term_memory 表：移除 user_id，新增 keywords / file_path 字段
  - 重建索引：idx_type_key（memory_type + key）、idx_importance（importance）

警告：此脚本会删除旧的 long_term_memory 表中的所有数据。
      执行前请确认旧表中没有需要保留的记忆数据。

使用方式：
  cd Sakura/backend/src
  python migrate_db.py
"""

import asyncio
from sqlalchemy import text
from db.database import engine
from db.models import Base


async def migrate():
    print("=" * 50)
    print("📦 长期记忆表结构迁移")
    print("=" * 50)

    async with engine.begin() as conn:
        # 1. 删除旧索引（MySQL 中需要先删除索引才能改表）
        print("\n[1/3] 删除旧表 long_term_memory ...")
        try:
            await conn.execute(text("DROP TABLE IF EXISTS long_term_memory"))
            print("     ✅ 旧表已删除")
        except Exception as e:
            print(f"     ⚠️  删除旧表时出现问题（可能不存在）: {e}")

        # 2. 重建所有表（按 models.py 中的定义）
        print("\n[2/3] 重建数据库表结构 ...")
        await conn.run_sync(Base.metadata.create_all)
        print("     ✅ 所有表已按新结构创建")

        # 3. 验证新表字段
        print("\n[3/3] 验证 long_term_memory 新表结构 ...")
        result = await conn.execute(text("DESCRIBE long_term_memory"))
        rows = result.fetchall()
        for row in rows:
            print(f"     字段: {row[0]:<15} 类型: {row[1]}")

    print("\n✅ 迁移完成！")
    print("📁 长期记忆将同时写入：")
    print("   - 数据库索引表（用于查找和去重）")
    print("   - Sakura/memory_store/*.md 文件（用于 LLM 读取）")
    print("=" * 50)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
