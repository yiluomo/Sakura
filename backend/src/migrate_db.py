"""
migrate_db.py
数据库表结构安全迁移脚本。

变更内容（2026-03-05）：
  - user_states 表：mood 改为 INT，新增 emotion_type / energy_level / emotion_updated_at 字段

安全机制：
  - 不修改或删除 long_term_memory 和 conversations 表
  - 不删除 memory_store/*.md 长期记忆文件
  - 仅重建 user_states 表以应用新字段

使用方式：
  cd Sakura/backend/src
  python migrate_db.py
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy import text
from db.database import engine
from db.models import Base

# Windows 下修复 Event loop is closed 错误
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def migrate():
    print("=" * 55)
    print("📦 数据库表结构安全迁移（情绪系统扩展）")
    print("=" * 55)

    async with engine.begin() as conn:

        # ── 步骤 1：删除旧的 user_states 表 ───────────────────────
        print("\n[1/4] 删除旧的 user_states 表...")
        try:
            await conn.execute(text("DROP TABLE IF EXISTS user_states"))
            print("     ✅ 旧的 user_states 表已删除")
        except Exception as e:
            print(f"     ⚠️  删除 user_states 表时出错: {e}")

        # ── 步骤 2：重建数据库表结构 ──────────────────────────────
        print("\n[2/4] 按新结构创建表（保留原有记录表）...")
        await conn.run_sync(Base.metadata.create_all)
        print("     ✅ metadata.create_all 执行完毕（已有表自动跳过）")

        # ── 步骤 3：验证 user_states 表结构 ────────────────────
        print("\n[3/4] 验证 user_states 表结构...")
        result = await conn.execute(text("DESCRIBE user_states"))
        for row in result.fetchall():
            print(f"       {row[0]:<25} {row[1]}")

        # ── 步骤 4：初始化默认用户状态 ─────────────────────────
        print("\n[4/4] 初始化默认用户状态...")
        try:
            await conn.execute(text("""
                INSERT INTO user_states (
                    user_id, affinity, mood, emotion_type, energy_level,
                    emotion_updated_at, last_interaction
                )
                VALUES ('依洛沐', 0, 50, 'calm', 80, NOW(), NOW())
                ON DUPLICATE KEY UPDATE user_id=user_id
            """))
            print("     ✅ 默认用户状态已初始化")
        except Exception as e:
            print(f"     ⚠️  初始化用户状态时出错: {e}")

    print("\n✅ 迁移完成！")
    print("   - user_states 情绪系统字段已添加：emotion_type, mood(INT), energy_level")
    print("   - 注意：长期记忆表、短期记忆表和对应的文件未被修改或删除。")
    print("=" * 55)

    # 关闭数据库连接
    try:
        await engine.dispose()
    except RuntimeError:
        pass


if __name__ == "__main__":
    asyncio.run(migrate())
