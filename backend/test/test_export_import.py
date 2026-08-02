"""
测试记忆导出/导入功能
"""
import asyncio
import json
from pathlib import Path
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.short_term import export_memories, import_memories
from db.database import AsyncSessionLocal
from db.crud import save_conversation, get_recent_conversations



async def test_export_import():
    """测试导出和导入功能"""
    user_id = "test_user"
    
    print("=" * 60)
    print("测试记忆导出/导入功能")
    print("=" * 60)
    
    # 1. 创建测试数据
    print("\n1. 创建测试数据...")
    async with AsyncSessionLocal() as db:
        await save_conversation(db, user_id, "user", "你好", emotion_type="calm", importance=3)
        await save_conversation(db, user_id, "sakura", "你好！", emotion_type="calm", importance=3)
        await save_conversation(db, user_id, "user", "今天天气不错", emotion_type="happy", importance=2)
        await save_conversation(db, user_id, "sakura", "是的，很适合出去走走", emotion_type="happy", importance=2)
    
    print("✅ 已创建 4 条测试对话")
    
    # 2. 导出记忆
    print("\n2. 导出记忆...")
    export_result = await export_memories(user_id, "test_export.json")
    
    exported_conv_count = 0
    if export_result["success"]:
        print(f"✅ 导出成功: {export_result['msg']}")
        print(f"   文件路径: {export_result['file_path']}")
        print(f"   导出数量: {export_result['count']}")
        
        # 验证导出文件
        with open(export_result['file_path'], 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            print(f"   版本: {export_data['version']}")
            print(f"   导出时间: {export_data['export_time']}")
            exported_conv_count = len(export_data.get('conversations', []))
    else:
        print(f"❌ 导出失败: {export_result['msg']}")
        return
    
    # 3. 清空数据（模拟数据丢失）
    print("\n3. 清空数据（模拟数据丢失）...")
    from db.crud import delete_conversations_by_ids
    async with AsyncSessionLocal() as db:
        convs = await get_recent_conversations(db, user_id, limit=1000)
        ids = [c["id"] for c in convs]
        if ids:
            await delete_conversations_by_ids(db, ids)
    print(f"✅ 已删除 {len(ids)} 条对话")
    
    # 4. 验证数据已清空
    async with AsyncSessionLocal() as db:
        remaining = await get_recent_conversations(db, user_id, limit=1000)
    print(f"   剩余对话数: {len(remaining)}")
    
    # 5. 导入记忆
    print("\n4. 导入记忆...")
    import_result = await import_memories(
        user_id=user_id,
        import_path="test_export.json",
        rebuild_vectors=False,  # 测试时不重建向量
        skip_existing=True
    )
    
    if import_result["success"]:
        print(f"✅ 导入成功: {import_result['msg']}")
        print(f"   导入数量: {import_result['imported_count']}")
        print(f"   跳过数量: {import_result['skipped_count']}")
    else:
        print(f"❌ 导入失败: {import_result['msg']}")
        return
    
    # 6. 验证导入结果
    print("\n5. 验证导入结果...")
    async with AsyncSessionLocal() as db:
        restored = await get_recent_conversations(db, user_id, limit=1000)
    
    print(f"   恢复对话数: {len(restored)}")
    if len(restored) == exported_conv_count:
        print("✅ 数据完整恢复")
    else:
        print(f"⚠️  数据不完整: 期望 {exported_conv_count}，实际 {len(restored)}")
    
    # 7. 清理测试文件
    print("\n6. 清理测试文件...")
    Path("test_export.json").unlink(missing_ok=True)
    print("✅ 测试完成")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_export_import())
