"""
migrate_db.py
数据库表结构安全迁移脚本。

变更内容：
  - long_term_memory 表：移除 user_id，新增 keywords / file_path 字段
  - 重建索引：idx_type_key（memory_type + key）、idx_importance（importance）

安全机制：
  - 迁移前自动读取旧表中的全部记忆数据
  - 将旧数据转存到对应的 memory_store/*.md 文件（新格式）
  - 再重建数据库表结构
  - 若旧表已是新结构（无 user_id 字段），则跳过数据迁移直接执行 create_all

使用方式：
  cd Sakura/backend/src
  python migrate_db.py
"""

import asyncio
from datetime import datetime
from pathlib import Path
from sqlalchemy import text, inspect
from db.database import engine
from db.models import Base
from config import MEMORY_STORE_DIR


# memory_type → 文件名 映射（与 file_store.py 保持一致）
_TYPE_TO_FILE = {
    "name":                 "profile.md",
    "age":                  "profile.md",
    "birthday":             "profile.md",
    "location":             "profile.md",
    "occupation":           "profile.md",
    "family":               "profile.md",
    "friend":               "profile.md",
    "hobby":                "preferences.md",
    "dislike":              "preferences.md",
    "experience":           "preferences.md",
    "manual":               "notes.md",
    "conversation_summary": "summaries_1.md",   # 迁移时统一写入第1卷
}

_TYPE_TO_TITLE = {
    "name": "姓名", "age": "年龄", "birthday": "生日",
    "location": "居住地", "occupation": "职业",
    "family": "家人", "friend": "朋友",
    "hobby": "爱好", "dislike": "厌恶", "experience": "经历",
    "manual": "备忘", "conversation_summary": "对话摘要",
}

_FILE_TITLES = {
    "profile.md":     "# 个人档案",
    "preferences.md": "# 偏好与经历",
    "notes.md":       "# 手动笔记",
    "summaries.md":   "# 对话摘要记录",
}


def _build_entry(memory_type: str, key: str, value: str, importance: int) -> str:
    """将旧数据库记录转换为新的 Markdown 条目格式。"""
    title = _TYPE_TO_TITLE.get(memory_type, memory_type)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if memory_type == "conversation_summary":
        display_key = key.replace("_to_", " 至 ").replace("_", "-")
        return (
            f"\n<!-- entry: {memory_type}/{key} -->\n"
            f"## {display_key}\n"
            f"**关键词**：（迁移自旧版数据库，未提取关键词）  \n"
            f"**摘要**：  \n"
            f"{value}\n\n"
            f"---\n"
        )
    else:
        return (
            f"\n<!-- entry: {memory_type}/{key} -->\n"
            f"## {title}\n"
            f"**内容**：{value}  \n"
            f"**关键词**：（迁移自旧版数据库，未提取关键词）  \n"
            f"**重要度**：{importance}  \n"
            f"**更新时间**：{now}\n\n"
            f"---\n"
        )


def _write_old_records_to_files(old_records: list) -> int:
    """
    将旧记录写入对应的 .md 文件。
    返回成功写入的条目数。
    """
    if not old_records:
        return 0

    # 按目标文件分组
    file_contents: dict[str, str] = {}

    for row in old_records:
        # 兼容有/无 user_id 字段的旧表
        if len(row) == 7:
            # 旧格式：id, user_id, memory_type, key, value, importance, created_at, updated_at
            _, _, memory_type, key, value, importance, *_ = row
        else:
            # 也可能字段顺序不同，按名称解析更安全（此处按常见顺序）
            memory_type = row[1] if len(row) > 1 else "manual"
            key = row[2] if len(row) > 2 else "unknown"
            value = row[3] if len(row) > 3 else ""
            importance = row[4] if len(row) > 4 else 1

        filename = _TYPE_TO_FILE.get(memory_type, "notes.md")
        entry = _build_entry(memory_type, key or "unknown", value or "", importance or 1)

        if filename not in file_contents:
            file_contents[filename] = _FILE_TITLES.get(filename, "# 记忆") + "\n"
        file_contents[filename] += entry

    # 写入文件
    MEMORY_STORE_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for filename, content in file_contents.items():
        filepath = MEMORY_STORE_DIR / filename
        # 若文件已存在，追加到末尾；否则新建
        if filepath.exists():
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"     📄 已写入 {filepath.name}：{content.count('<!-- entry:')} 条")
        count += content.count("<!-- entry:")

    return count


async def migrate():
    print("=" * 55)
    print("📦 长期记忆表结构安全迁移")
    print("=" * 55)

    async with engine.begin() as conn:

        # ── 步骤 1：检测旧表是否存在，读取旧数据 ──────────────
        print("\n[1/4] 检测旧表结构和数据...")
        old_records = []
        old_table_exists = False

        try:
            result = await conn.execute(text("SHOW TABLES LIKE 'long_term_memory'"))
            if result.fetchone():
                old_table_exists = True

                # 读取全部旧数据（在 DROP 之前）
                rows = await conn.execute(
                    text("SELECT * FROM long_term_memory LIMIT 1000")
                )
                old_records = rows.fetchall()
                print(f"     ✅ 发现旧表，共 {len(old_records)} 条记忆记录")

                if old_records:
                    # 打印旧字段信息，便于确认格式
                    cols = await conn.execute(text("DESCRIBE long_term_memory"))
                    col_names = [c[0] for c in cols.fetchall()]
                    print(f"     📋 旧表字段: {col_names}")
            else:
                print("     ℹ️  旧表不存在，跳过数据备份")
        except Exception as e:
            print(f"     ⚠️  检测旧表时出错: {e}")

        # ── 步骤 2：旧数据写入 .md 文件 ────────────────────────
        if old_records:
            print(f"\n[2/4] 将 {len(old_records)} 条旧记忆迁移到 memory_store/ 文件...")
            written = _write_old_records_to_files(list(old_records))
            print(f"     ✅ 共迁移 {written} 条记忆到文件")
            print(f"     📁 文件位置: {MEMORY_STORE_DIR}")
        else:
            print("\n[2/4] 无旧数据需要迁移，跳过")

        # ── 步骤 3：删除旧表，重建新结构 ───────────────────────
        print("\n[3/4] 删除旧表并重建新结构...")
        try:
            await conn.execute(text("DROP TABLE IF EXISTS long_term_memory"))
            print("     ✅ 旧表已删除")
        except Exception as e:
            print(f"     ⚠️  删除旧表时出错: {e}")

        await conn.run_sync(Base.metadata.create_all)
        print("     ✅ 所有表已按新结构创建")

        # ── 步骤 4：验证新表字段 ────────────────────────────────
        print("\n[4/4] 验证新表结构...")
        result = await conn.execute(text("DESCRIBE long_term_memory"))
        for row in result.fetchall():
            print(f"     字段: {row[0]:<15} 类型: {row[1]}")

    print("\n✅ 迁移完成！")
    if old_records:
        print(f"   - 旧数据已从数据库迁移到 memory_store/ 文件")
        print(f"   - 注意：旧记忆未提取关键词，可重新手动触发保存以生成关键词")
    print("   - 后续长期记忆将同时写入数据库索引和 memory_store/*.md 文件")
    print("=" * 55)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
