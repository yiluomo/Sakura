"""
rebuild_index.py
记忆索引重建模块

功能：扫描 memory_store/ 目录下的所有 .md 文件，
将未建立数据库索引的记忆条目导入数据库。

使用场景：
1. 迁移后自动重建索引
2. 手动编辑 .md 文件后重建索引
3. 数据库索引丢失后恢复
"""

from pathlib import Path
from typing import List, Dict
from db.database import get_db_session
from db.crud import check_memory_exists, save_or_update_long_term_memory
from memory.file_store import _parse_entries_from_file
from config import MEMORY_STORE_DIR
import aiofiles


async def rebuild_all_indexes() -> Dict[str, int]:
    """
    扫描所有 .md 文件，重建数据库索引
    
    返回：
        {
            "total": 总条目数,
            "new": 新建索引数,
            "updated": 更新索引数,
            "skipped": 跳过数（已存在且未变化）
        }
    """
    stats = {
        "total": 0,
        "new": 0,
        "updated": 0,
        "skipped": 0
    }
    
    async with get_db_session() as db:
        # 1. 处理固定文件
        for filename in ["profile.md", "preferences.md", "notes.md"]:
            filepath = MEMORY_STORE_DIR / filename
            if not filepath.exists():
                continue
            
            async with aiofiles.open(filepath, encoding="utf-8") as f:
                text = await f.read()
            
            entries = _parse_entries_from_file(text)
            for entry in entries:
                stats["total"] += 1
                
                # 检查是否已存在
                existing = await check_memory_exists(db, entry["memory_type"], entry["key"])
                
                # 写入或更新索引
                await save_or_update_long_term_memory(
                    db,
                    memory_type=entry["memory_type"],
                    key=entry["key"],
                    value=entry["content"],
                    keywords=" ".join(entry["keywords"]),
                    file_path=f"memory_store/{filename}",
                    importance=entry["importance"],
                    emotion_tag="",  # 旧记忆无情绪标签
                    emotional_intensity=0
                )
                
                if existing:
                    stats["updated"] += 1
                else:
                    stats["new"] += 1
        
        # 2. 处理所有 summaries_N.md 文件
        for filepath in MEMORY_STORE_DIR.glob("summaries_*.md"):
            if not filepath.exists():
                continue
            
            async with aiofiles.open(filepath, encoding="utf-8") as f:
                text = await f.read()
            
            entries = _parse_entries_from_file(text)
            for entry in entries:
                stats["total"] += 1
                
                # 检查是否已存在
                existing = await check_memory_exists(db, entry["memory_type"], entry["key"])
                
                # 写入或更新索引
                await save_or_update_long_term_memory(
                    db,
                    memory_type=entry["memory_type"],
                    key=entry["key"],
                    value=entry["content"],
                    keywords=" ".join(entry["keywords"]),
                    file_path=f"memory_store/{filepath.name}",
                    importance=entry["importance"],
                    emotion_tag="",
                    emotional_intensity=0
                )
                
                if existing:
                    stats["updated"] += 1
                else:
                    stats["new"] += 1
    
    return stats


async def find_unindexed_entries() -> List[Dict]:
    """
    查找文件中存在但数据库中不存在的记忆条目
    
    返回：未建立索引的条目列表
    """
    unindexed = []
    
    async with get_db_session() as db:
        # 1. 检查固定文件
        for filename in ["profile.md", "preferences.md", "notes.md"]:
            filepath = MEMORY_STORE_DIR / filename
            if not filepath.exists():
                continue
            
            async with aiofiles.open(filepath, encoding="utf-8") as f:
                text = await f.read()
            
            entries = _parse_entries_from_file(text)
            for entry in entries:
                existing = await check_memory_exists(db, entry["memory_type"], entry["key"])
                if not existing:
                    unindexed.append({
                        **entry,
                        "file": filename
                    })
        
        # 2. 检查所有 summaries_N.md 文件
        for filepath in MEMORY_STORE_DIR.glob("summaries_*.md"):
            if not filepath.exists():
                continue
            
            async with aiofiles.open(filepath, encoding="utf-8") as f:
                text = await f.read()
            
            entries = _parse_entries_from_file(text)
            for entry in entries:
                existing = await check_memory_exists(db, entry["memory_type"], entry["key"])
                if not existing:
                    unindexed.append({
                        **entry,
                        "file": filepath.name
                    })
    
    return unindexed


async def index_single_entry(memory_type: str, key: str, file_path: str) -> bool:
    """
    为单个记忆条目建立索引
    
    参数：
        memory_type: 记忆类型
        key: 记忆键
        file_path: 文件路径（相对于 memory_store/）
    
    返回：是否成功
    """
    filepath = MEMORY_STORE_DIR / file_path.replace("memory_store/", "")
    if not filepath.exists():
        return False
    
    async with aiofiles.open(filepath, encoding="utf-8") as f:
        text = await f.read()
    
    entries = _parse_entries_from_file(text)
    target_entry = None
    
    for entry in entries:
        if entry["memory_type"] == memory_type and entry["key"] == key:
            target_entry = entry
            break
    
    if not target_entry:
        return False
    
    async with get_db_session() as db:
        await save_or_update_long_term_memory(
            db,
            memory_type=target_entry["memory_type"],
            key=target_entry["key"],
            value=target_entry["content"],
            keywords=" ".join(target_entry["keywords"]),
            file_path=file_path,
            importance=target_entry["importance"],
            emotion_tag="",
            emotional_intensity=0
        )
    
    return True
