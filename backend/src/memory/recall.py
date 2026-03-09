"""
recall.py
记忆召回模块（集成向量检索）

召回策略：
1. 短期记忆：最近 6 轮对话（用于上下文连贯）
2. 向量记忆：语义相似的 5 条对话（用于相关回忆）
3. 长期记忆：手动标记的重要信息（profile/preferences/notes）
"""

from memory.short_term import get_recent
from memory.long_term import get_profile
from memory.vector_store import search_similar_conversations
from config import RECALL_SHORT_TERM_LIMIT, RECALL_VECTOR_LIMIT, RECALL_LONG_TERM_LIMIT


async def recall_context(user_id: str, current_message: str = "") -> dict:
    """
    召回记忆上下文
    
    Args:
        user_id: 用户 ID
        current_message: 当前用户消息（用于向量检索）
        
    Returns:
        {
            "short_term": List[dict],  # 最近对话
            "vector_memory": List[dict],  # 语义相关对话
            "long_term": str  # 长期记忆文本
        }
    """
    # 1. 短期记忆（最近 N 轮对话）
    short_term = await get_recent(user_id, limit=RECALL_SHORT_TERM_LIMIT)
    
    # 2. 向量记忆（语义相似对话）
    vector_memory = []
    if current_message:
        vector_results = await search_similar_conversations(
            user_id=user_id,
            query_text=current_message,
            limit=RECALL_VECTOR_LIMIT,
        )
        vector_memory = vector_results
    
    # 3. 长期记忆（手动标记的重要信息）
    long_term = await get_profile(user_id)
    
    return {
        "short_term": short_term,
        "vector_memory": vector_memory,
        "long_term": long_term
    }