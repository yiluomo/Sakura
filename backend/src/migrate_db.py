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
from db.models import UserState

# Windows 下修复 Event loop is closed 错误
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def migrate():
    print("=" * 55)
    print("📦 数据库表结构安全迁移（情绪系统扩展）")
    print("=" * 55)

    async with engine.begin() as conn:

        # ── 步骤 1：确保 user_states 表存在（不触碰其他表） ─────────
        print("\n[1/4] 检查/创建 user_states 表...")
        try:
            await conn.run_sync(UserState.__table__.create, checkfirst=True)
            print("     ✅ user_states 表已就绪")
        except Exception as e:
            print(f"     ⚠️  创建 user_states 表时出错: {e}")

        # ── 步骤 2：就地迁移字段（仅 ALTER user_states，不删除数据） ──
        print("\n[2/4] 就地迁移 user_states 字段...")
        alter_statements = [
            "ALTER TABLE user_states MODIFY COLUMN mood INT DEFAULT 50",
            "ALTER TABLE user_states ADD COLUMN emotion_type VARCHAR(20) DEFAULT 'calm'",
            "ALTER TABLE user_states ADD COLUMN energy_level INT DEFAULT 80",
            "ALTER TABLE user_states ADD COLUMN emotion_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE user_states ADD COLUMN last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP",
        ]

        for sql in alter_statements:
            try:
                await conn.execute(text(sql))
                print(f"     ✅ {sql}")
            except Exception as e:
                # 已存在 / 类型已是 INT 等情况会报错，这里视为可接受
                print(f"     ⏭️  跳过: {sql} ({e})")

        # 回填历史空值，避免运行时出现 None
        try:
            await conn.execute(text(
                "UPDATE user_states SET last_interaction = NOW() WHERE last_interaction IS NULL"
            ))
            await conn.execute(text(
                "UPDATE user_states SET emotion_updated_at = NOW() WHERE emotion_updated_at IS NULL"
            ))
        except Exception as e:
            print(f"     ⚠️  回填时间字段时出错: {e}")

        # ── 步骤 3：验证 user_states 表结构 ─────────────────────
        print("\n[3/4] 验证 user_states 表结构...")
        try:
            result = await conn.execute(text("DESCRIBE user_states"))
            for row in result.fetchall():
                print(f"       {row[0]:<25} {row[1]}")
        except Exception as e:
            print(f"     ⚠️  DESCRIBE user_states 失败: {e}")

        # ── 步骤 4：初始化默认用户状态（不覆盖已有数据） ──────────
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
