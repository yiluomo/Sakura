"""
测试记忆归档功能，验证归档合并总结、对话倒序和单记录聚合保存。
"""
import asyncio
import sys
import os
import io
from datetime import datetime, timedelta

# 强制设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db.database import init_db, AsyncSessionLocal
from db.models import Conversation, LongTermMemory
from api.memory import _do_archive
from memory import file_store
from sqlalchemy import select, delete

async def test_archiving_flow():
    print("=" * 50)
    print("开始测试记忆系统聚合归档功能")
    print("=" * 50)

    user_id = "测试归档用户"

    async with AsyncSessionLocal() as db:
        # 清理之前的脏数据
        await db.execute(delete(Conversation).where(Conversation.user_id == user_id))
        await db.commit()

        # 1. 插入多条模拟对话历史（时间顺序：旧 -> 新）
        base_time = datetime.now() - timedelta(hours=1)
        convs = [
            Conversation(
                user_id=user_id,
                role="user",
                content="我喜欢在周末去图书馆看书，特别是科幻小说。",
                timestamp=base_time,
                emotion_type="calm",
                importance=3
            ),
            Conversation(
                user_id=user_id,
                role="sakura",
                content="科幻小说很有意思呢！那你有最喜欢的科幻小说作家吗？",
                timestamp=base_time + timedelta(minutes=2),
                emotion_type="happy",
                importance=3
            ),
            Conversation(
                user_id=user_id,
                role="user",
                content="我最喜欢刘慈欣，他的《三体》非常震撼。",
                timestamp=base_time + timedelta(minutes=5),
                emotion_type="calm",
                importance=4
            ),
        ]
        for c in convs:
            db.add(c)
        await db.commit()
        print("✓ 已成功插入3条模拟短期记忆")

    # 2. 执行归档
    print("🔄 开始执行归档...")
    result = await _do_archive(user_id)
    print(f"归档返回结果: {result}")

    # 验证归档是否成功
    assert result["success"] is True, "归档流程应执行成功"
    assert result["data"]["archived_count"] == 3, "应该成功归档3条对话"

    # 3. 验证数据库中的归档长期记忆记录
    async with AsyncSessionLocal() as db:
        # 查出刚才归档生成的长期记忆记录
        stmt = select(LongTermMemory).where(LongTermMemory.memory_type == "archived_conversation")
        res = await db.execute(stmt)
        lt_memories = res.scalars().all()

        # 找到包含该时间戳或带有最新 key 的记录
        target_memory = None
        for m in lt_memories:
            if m.key.startswith("archive_") and "刘慈欣" in m.value:
                target_memory = m
                break

        assert target_memory is not None, "数据库中应至少有1条带 archive_ 前缀的聚合长期记忆"
        
        print("\n=== 数据库长期记忆记录验证 ===")
        print(f"✓ Key: {target_memory.key}")
        print(f"✓ Keywords: {target_memory.keywords}")
        print(f"✓ File Path: {target_memory.file_path}")
        print(f"Value 内容预览:\n{target_memory.value}")
        print("==============================\n")

        # 验证倒序排列
        val_lines = target_memory.value.split("\n")
        user_line_index = -1
        sakura_line_index = -1
        
        for idx, line in enumerate(val_lines):
            if "刘慈欣" in line:
                user_line_index = idx
            elif "科幻小说作家" in line:
                sakura_line_index = idx
                
        assert user_line_index != -1 and sakura_line_index != -1, "原对话应该存在于记录中"
        assert user_line_index < sakura_line_index, "较晚的对话（刘慈欣）应该排在较早的对话（科幻小说作家）前面（即倒序）"
        print("✓ 对话详情时间倒序排列验证成功！较晚对话排在较早对话上方。")

        # 验证总结段落
        assert "【对话总结】" in target_memory.value, "聚合记忆中应包含【对话总结】"
        assert "【对话详情（倒序）】" in target_memory.value, "聚合记忆中应包含【对话详情（倒序）】"
        print("✓ 对话总结及分类标签提取验证成功！")

        # 验证短期记忆被删除
        stmt_conv = select(Conversation).where(Conversation.user_id == user_id)
        res_conv = await db.execute(stmt_conv)
        convs_left = res_conv.scalars().all()
        assert len(convs_left) == 0, "被归档的短期记忆应该已经从 conversations 表中删除"
        print("✓ 短期记忆表清理验证成功！")

        # 4. 清理测试数据
        print("\n🧹 开始清理测试产生的临时数据...")
        await db.delete(target_memory)
        await db.commit()
        
        # 清理 file_store 中的物理记录
        await file_store.delete_entry("archived_conversation", target_memory.key)
        print("✓ 测试临时数据清理完成。")

async def main():
    # 初始化数据库
    await init_db()
    await test_archiving_flow()
    print("\n" + "=" * 50)
    print("所有归档功能测试用例全部通过！")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
