"""
short_term.py (重构为 recent.py)
短期记忆模块 - 提供最近对话查询和记忆导出/导入功能

RAG 方案中：
- 所有对话保留在 MySQL 数据库中
- 向量索引存储在 Qdrant 中
- 不再需要自动压缩归档

本模块提供：
1. 查询最近对话
2. 导出记忆（用于备份）
3. 导入记忆（用于迁移/恢复）
"""

from db.database import AsyncSessionLocal
from db.crud import (
    get_recent_conversations,
    count_conversations,
    save_conversation,
)
from memory.vector_store import add_conversation_vector
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Any


async def get_recent(user_id: str, limit: int = 50):
    """获取最近的对话"""
    async with AsyncSessionLocal() as db:
        return await get_recent_conversations(db, user_id, limit)


async def get_conversation_count(user_id: str) -> int:
    """获取对话次数"""
    async with AsyncSessionLocal() as db:
        return await count_conversations(db, user_id)


async def export_memories(user_id: str, output_path: str = None) -> Dict[str, Any]:
    """
    导出用户的所有记忆数据（用于备份或迁移）
    
    导出内容：
    1. MySQL 中的所有对话记录（短期记忆）
    2. MySQL 中的所有长期记忆记录
    3. 导出时间戳和统计信息
    
    注意：
    - 向量数据不导出（可以从 MySQL 重建）
    - memory_store/*.md 文件需要手动备份
    
    Args:
        user_id: 用户 ID
        output_path: 输出文件路径（默认为 memory_exports/memory_export_{user_id}_{timestamp}.json）
        
    Returns:
        {"success": bool, "msg": str, "file_path": str, "count": int}
    """
    try:
        async with AsyncSessionLocal() as db:
            # 1. 获取所有对话记录（短期记忆）
            all_conversations = await get_recent_conversations(db, user_id, limit=100000)
            
            # 2. 获取所有长期记忆记录
            from db.crud import get_long_term_memories
            all_long_term = await get_long_term_memories(db, memory_type=None, limit=100000)
            
            # 转换长期记忆为可序列化格式
            long_term_data = [
                {
                    "id": mem.id,
                    "memory_type": mem.memory_type,
                    "key": mem.key,
                    "value": mem.value,
                    "keywords": mem.keywords,
                    "file_path": mem.file_path,
                    "importance": mem.importance,
                    "emotion_tag": mem.emotion_tag,
                    "emotional_intensity": mem.emotional_intensity,
                    "created_at": mem.created_at.isoformat() if mem.created_at else None,
                    "updated_at": mem.updated_at.isoformat() if mem.updated_at else None
                }
                for mem in all_long_term
            ]
        
        if not all_conversations and not long_term_data:
            return {
                "success": False,
                "msg": "没有可导出的记忆数据",
                "file_path": None,
                "count": 0
            }
        
        # 3. 构建导出数据
        export_data = {
            "version": "1.0",
            "export_time": datetime.now().isoformat(),
            "user_id": user_id,
            "short_term_count": len(all_conversations),
            "long_term_count": len(long_term_data),
            "conversations": all_conversations,
            "long_term_memories": long_term_data
        }
        
        # 4. 确定输出路径（默认导出到根目录的 memory_exports）
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"../../memory_exports/memory_export_{user_id}_{timestamp}.json"
        
        # 5. 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        msg = f"已导出 {len(all_conversations)} 条对话记录和 {len(long_term_data)} 条长期记忆"
        print(f"✅ [export_memories] {msg} -> {output_path}")
        
        return {
            "success": True,
            "msg": msg,
            "file_path": str(output_file.absolute()),
            "count": len(all_conversations) + len(long_term_data)
        }
        
    except Exception as e:
        print(f"❌ [export_memories] 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "msg": f"导出失败：{str(e)}",
            "file_path": None,
            "count": 0
        }


async def import_memories(
    user_id: str,
    import_path: str,
    rebuild_vectors: bool = True,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    导入记忆数据（用于迁移或恢复）
    
    导入流程：
    1. 读取导出的 JSON 文件
    2. 将对话记录导入 MySQL（短期记忆）
    3. 将长期记忆记录导入 MySQL
    4. 可选：重建向量索引
    
    Args:
        user_id: 用户 ID
        import_path: 导入文件路径
        rebuild_vectors: 是否重建向量索引（默认 True）
        skip_existing: 是否跳过已存在的记录（默认 True，避免重复导入）
        
    Returns:
        {"success": bool, "msg": str, "imported_count": int, "skipped_count": int}
    """
    try:
        # 1. 读取导入文件
        import_file = Path(import_path)
        if not import_file.exists():
            return {
                "success": False,
                "msg": f"导入文件不存在: {import_path}",
                "imported_count": 0,
                "skipped_count": 0
            }
        
        with open(import_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # 2. 验证数据格式
        conversations = import_data.get("conversations", [])
        long_term_memories = import_data.get("long_term_memories", [])
        
        if not conversations and not long_term_memories:
            return {
                "success": False,
                "msg": "导入文件格式错误：没有找到记忆数据",
                "imported_count": 0,
                "skipped_count": 0
            }
        
        # 3. 导入短期记忆（对话记录）
        imported_conversations = 0
        skipped_conversations = 0
        conversation_ids = []
        
        if conversations:
            # 获取已存在的对话（用于去重）
            existing_timestamps = set()
            if skip_existing:
                async with AsyncSessionLocal() as db:
                    existing_convs = await get_recent_conversations(db, user_id, limit=100000)
                    existing_timestamps = {
                        (conv["timestamp"], conv["role"], conv["content"])
                        for conv in existing_convs
                    }
            
            async with AsyncSessionLocal() as db:
                for conv in conversations:
                    # 检查是否已存在
                    conv_key = (conv["timestamp"], conv["role"], conv["content"])
                    if skip_existing and conv_key in existing_timestamps:
                        skipped_conversations += 1
                        continue
                    
                    # 导入对话
                    conv_id = await save_conversation(
                        db,
                        user_id=user_id,
                        role=conv["role"],
                        content=conv["content"],
                        emotion_type=conv.get("emotion_type", "calm"),
                        importance=conv.get("importance", 3),
                        timestamp=datetime.fromisoformat(conv["timestamp"])
                    )
                    
                    conversation_ids.append({
                        "id": conv_id,
                        "role": conv["role"],
                        "content": conv["content"],
                        "emotion_type": conv.get("emotion_type", "calm"),
                        "importance": conv.get("importance", 3)
                    })
                    
                    imported_conversations += 1
        
        # 4. 导入长期记忆
        imported_long_term = 0
        skipped_long_term = 0
        long_term_ids = []
        
        if long_term_memories:
            from db.crud import save_or_update_long_term_memory, check_memory_exists
            
            async with AsyncSessionLocal() as db:
                for mem in long_term_memories:
                    # 检查是否已存在
                    if skip_existing:
                        existing = await check_memory_exists(
                            db, mem["memory_type"], mem["key"]
                        )
                        if existing:
                            skipped_long_term += 1
                            continue
                    
                    # 导入长期记忆
                    await save_or_update_long_term_memory(
                        db,
                        memory_type=mem["memory_type"],
                        key=mem["key"],
                        value=mem["value"],
                        keywords=mem.get("keywords", ""),
                        file_path=mem.get("file_path", ""),
                        importance=mem.get("importance", 3),
                        emotion_tag=mem.get("emotion_tag", ""),
                        emotional_intensity=mem.get("emotional_intensity", 0)
                    )
                    
                    # 获取刚插入的记忆ID
                    inserted = await check_memory_exists(
                        db, mem["memory_type"], mem["key"]
                    )
                    if inserted:
                        long_term_ids.append({
                            "id": inserted.id,
                            "content": mem["value"],
                            "importance": mem.get("importance", 3)
                        })
                    
                    imported_long_term += 1
        
        # 5. 重建向量索引（可选）
        vector_count = 0
        if rebuild_vectors:
            # 为短期记忆生成向量
            if conversation_ids:
                print(f"🔄 开始为 {len(conversation_ids)} 条对话生成向量...")
                for conv_data in conversation_ids:
                    try:
                        vector_id = await add_conversation_vector(
                            user_id=user_id,
                            conversation_id=conv_data["id"],
                            role=conv_data["role"],
                            content=conv_data["content"],
                            emotion_type=conv_data["emotion_type"],
                            importance=conv_data["importance"]
                        )
                        if vector_id:
                            vector_count += 1
                    except Exception as e:
                        print(f"⚠️  对话向量生成失败 (id={conv_data['id']}): {e}")
            
            # 为长期记忆生成向量
            if long_term_ids:
                print(f"🔄 开始为 {len(long_term_ids)} 条长期记忆生成向量...")
                for mem_data in long_term_ids:
                    try:
                        vector_id = await add_conversation_vector(
                            user_id=user_id,
                            conversation_id=mem_data["id"],
                            role="long_term_memory",
                            content=mem_data["content"],
                            emotion_type="calm",
                            importance=mem_data["importance"]
                        )
                        if vector_id:
                            vector_count += 1
                    except Exception as e:
                        print(f"⚠️  长期记忆向量生成失败 (id={mem_data['id']}): {e}")
            
            print(f"✅ 向量索引重建完成: {vector_count} 条")
        
        total_imported = imported_conversations + imported_long_term
        total_skipped = skipped_conversations + skipped_long_term
        
        msg = f"导入完成：新增 {total_imported} 条（对话{imported_conversations}+长期记忆{imported_long_term}），跳过 {total_skipped} 条"
        if rebuild_vectors:
            msg += f"，重建向量 {vector_count} 条"
        
        print(f"✅ [import_memories] {msg}")
        
        return {
            "success": True,
            "msg": msg,
            "imported_count": total_imported,
            "skipped_count": total_skipped,
            "vector_count": vector_count if rebuild_vectors else 0
        }
        
    except Exception as e:
        print(f"❌ [import_memories] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "msg": f"导入失败：{str(e)}",
            "imported_count": 0,
            "skipped_count": 0
        }

