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


async def get_recent(user_id: str, limit: int = 6):
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
    1. MySQL 中的所有对话记录（包含 emotion_type, importance, vector_id）
    2. 导出时间戳和统计信息
    
    注意：
    - Qdrant 向量数据不导出（可以从 MySQL 重建）
    - memory_store/*.md 文件需要手动备份
    
    Args:
        user_id: 用户 ID
        output_path: 输出文件路径（默认为 memory_export_{user_id}_{timestamp}.json）
        
    Returns:
        {"success": bool, "msg": str, "file_path": str, "count": int}
    """
    try:
        # 1. 获取所有对话记录
        async with AsyncSessionLocal() as db:
            all_conversations = await get_recent_conversations(db, user_id, limit=100000)
        
        if not all_conversations:
            return {
                "success": False,
                "msg": "没有可导出的对话记录",
                "file_path": None,
                "count": 0
            }
        
        # 2. 构建导出数据
        export_data = {
            "version": "1.0",
            "export_time": datetime.now().isoformat(),
            "user_id": user_id,
            "total_count": len(all_conversations),
            "conversations": all_conversations
        }
        
        # 3. 确定输出路径
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"memory_export_{user_id}_{timestamp}.json"
        
        # 4. 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        msg = f"已导出 {len(all_conversations)} 条对话记录"
        print(f"✅ [export_memories] {msg} -> {output_path}")
        
        return {
            "success": True,
            "msg": msg,
            "file_path": str(output_file.absolute()),
            "count": len(all_conversations)
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
    2. 将对话记录导入 MySQL
    3. 可选：重建 Qdrant 向量索引
    
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
        if "conversations" not in import_data:
            return {
                "success": False,
                "msg": "导入文件格式错误：缺少 conversations 字段",
                "imported_count": 0,
                "skipped_count": 0
            }
        
        conversations = import_data["conversations"]
        
        # 3. 获取已存在的对话（用于去重）
        existing_timestamps = set()
        if skip_existing:
            async with AsyncSessionLocal() as db:
                existing_convs = await get_recent_conversations(db, user_id, limit=100000)
                existing_timestamps = {
                    (conv["timestamp"], conv["role"], conv["content"])
                    for conv in existing_convs
                }
        
        # 4. 导入对话记录
        imported_count = 0
        skipped_count = 0
        conversation_ids = []  # 用于后续重建向量
        
        async with AsyncSessionLocal() as db:
            for conv in conversations:
                # 检查是否已存在（基于时间戳+角色+内容去重）
                conv_key = (conv["timestamp"], conv["role"], conv["content"])
                if skip_existing and conv_key in existing_timestamps:
                    skipped_count += 1
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
                
                imported_count += 1
        
        # 5. 重建向量索引（可选）
        vector_count = 0
        if rebuild_vectors and conversation_ids:
            print(f"🔄 开始重建 {len(conversation_ids)} 条对话的向量索引...")
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
                    print(f"⚠️  向量生成失败 (id={conv_data['id']}): {e}")
            
            print(f"✅ 向量索引重建完成: {vector_count}/{len(conversation_ids)}")
        
        msg = f"导入完成：新增 {imported_count} 条，跳过 {skipped_count} 条"
        if rebuild_vectors:
            msg += f"，重建向量 {vector_count} 条"
        
        print(f"✅ [import_memories] {msg}")
        
        return {
            "success": True,
            "msg": msg,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
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

