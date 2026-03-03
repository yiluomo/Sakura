"""
long_term.py
长期记忆模块（重构版）。

职责分工：
- 数据库：存储轻量索引（memory_type / key / keywords / file_path / importance）
- 文件：存储完整的 Markdown 格式记忆内容（memory_store/*.md）
- LLM：在写入时提取 5~10 个检索关键词

写入流程（confirm_save_memory / save_memory）：
  1. LLM 提取关键词
  2. 文件写入（file_store.write_entry）
  3. 数据库写入/更新索引（db/crud.save_or_update_long_term_memory）

读取流程（get_profile → 注入 prompt）：
  → 读取文件（file_store.get_top_memories），内容完整、LLM 友好
"""

from db.database import AsyncSessionLocal
from db.crud import save_or_update_long_term_memory, check_memory_exists
from memory.keyword_extractor import extract_keywords, keywords_to_str
from memory import file_store
from datetime import datetime
from typing import Optional, Dict


# ─────────────────────────────────────────────
# 手动保存（直接调用，不需要前端确认）
# ─────────────────────────────────────────────

async def save_memory(user_id: str, content: str):
    """手动保存长期记忆（manual 类型）"""
    memory_type = "manual"
    key = "user_note"

    keywords = await extract_keywords(content)
    kw_str = keywords_to_str(keywords)
    rel_path = file_store.get_relative_path(memory_type)

    # 写入文件
    await file_store.write_entry(memory_type, key, content, keywords, importance=5)

    # 写入数据库索引
    async with AsyncSessionLocal() as db:
        await save_or_update_long_term_memory(
            db, memory_type, key, content, kw_str, rel_path, importance=5
        )


# ─────────────────────────────────────────────
# 触发检测（检查用户消息是否含"记住…"）
# ─────────────────────────────────────────────

async def check_memory_trigger(user_id: str, user_msg: str) -> Optional[Dict]:
    """
    检测是否触发记忆保存，返回记忆信息用于前端确认。
    不执行实际写入，不影响对话回复流程。
    """
    if not user_msg.startswith("记住"):
        return None

    content = user_msg[2:].strip()
    memory_info = _detect_memory_type(content)

    if memory_info:
        async with AsyncSessionLocal() as db:
            existing = await check_memory_exists(
                db, memory_info["type"], memory_info["key"]
            )
            if existing:
                return {
                    "action":      "update",
                    "memory_type": memory_info["type"],
                    "key":         memory_info["key"],
                    "old_value":   existing.value,
                    "new_value":   content,
                    "importance":  memory_info["importance"],
                }
            else:
                return {
                    "action":      "create",
                    "memory_type": memory_info["type"],
                    "key":         memory_info["key"],
                    "value":       content,
                    "importance":  memory_info["importance"],
                }
    else:
        # 未检测到具体类型 → 通用手动记忆
        return {
            "action":      "create",
            "memory_type": "manual",
            "key":         "user_note",
            "value":       content,
            "importance":  3,
        }


def _detect_memory_type(content: str) -> Optional[Dict]:
    """检测记忆类型和对应关键词（不变）"""
    keywords_map = {
        "name":       {"keywords": ["我叫", "我的名字", "叫我", "我是"],            "importance": 5},
        "hobby":      {"keywords": ["我喜欢", "我爱", "我的爱好", "我喜爱"],         "importance": 4},
        "dislike":    {"keywords": ["我讨厌", "我不喜欢", "我厌恶"],                "importance": 4},
        "family":     {"keywords": ["我的家人", "我的父母", "我的爸爸", "我的妈妈",
                                    "我的兄弟", "我的姐妹"],                         "importance": 5},
        "friend":     {"keywords": ["我的朋友", "我的好友"],                        "importance": 4},
        "birthday":   {"keywords": ["我的生日", "我生日", "我出生"],                "importance": 5},
        "age":        {"keywords": ["我今年", "我的年龄", "我多大"],                "importance": 4},
        "location":   {"keywords": ["我住在", "我来自", "我在", "我的家乡"],        "importance": 4},
        "occupation": {"keywords": ["我的工作", "我是", "我做", "我的职业"],        "importance": 4},
        "experience": {"keywords": ["我曾经", "我以前", "我经历过"],               "importance": 3},
    }

    for memory_type, info in keywords_map.items():
        for keyword in info["keywords"]:
            if keyword in content:
                return {
                    "type":       memory_type,
                    "key":        keyword,
                    "importance": info["importance"],
                }
    return None


# ─────────────────────────────────────────────
# 前端确认后写入
# ─────────────────────────────────────────────

async def confirm_save_memory(user_id: str, memory_info: Dict) -> bool:
    """
    用户从前端确认后，正式写入记忆（文件 + 数据库索引）。
    
    流程：
      1. LLM 提取关键词
      2. 写入对应 .md 文件
      3. 写入/更新数据库索引
    """
    memory_type = memory_info["memory_type"]
    key         = memory_info["key"]
    importance  = memory_info.get("importance", 3)

    # 区分新建和更新时的内容字段名
    content = memory_info.get("new_value") or memory_info.get("value", "")

    try:
        # 1. LLM 提取关键词（失败时降级为空列表）
        keywords = await extract_keywords(content)
        kw_str   = keywords_to_str(keywords)
        rel_path = file_store.get_relative_path(memory_type)

        # 2. 写入 .md 文件
        await file_store.write_entry(memory_type, key, content, keywords, importance)

        # 3. 写入/更新数据库索引
        async with AsyncSessionLocal() as db:
            await save_or_update_long_term_memory(
                db, memory_type, key, content, kw_str, rel_path, importance
            )

        print(f"✅ [long_term] 记忆已保存: [{memory_type}/{key}] 关键词: {kw_str}")
        return True

    except Exception as e:
        print(f"❌ [long_term] 记忆保存失败: {e}")
        return False


# ─────────────────────────────────────────────
# 读取记忆 → 注入 prompt
# ─────────────────────────────────────────────

async def get_profile(user_id: str) -> str:
    """
    获取用户长期记忆，用于注入对话 prompt。
    从 .md 文件读取完整内容，按重要度取前5条，格式化为 LLM 友好文本。
    """
    return await file_store.get_top_memories(n=5)
