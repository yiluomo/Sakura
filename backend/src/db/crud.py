from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Conversation, LongTermMemory, UserState
from datetime import datetime
from typing import Optional, List


# ========== 对话历史 ==========

async def save_conversation(
    db: AsyncSession,
    user_id: str,
    role: str,
    content: str,
    vector_id: str = "",
    emotion_type: str = "calm",
    importance: int = 3,
    timestamp: Optional[datetime] = None
) -> int:
    """
    保存一条对话
    
    Args:
        timestamp: 可选的时间戳，用于导入历史数据（默认使用当前时间）
    
    Returns:
        conversation_id: 对话 ID
    """
    conv = Conversation(
        user_id=user_id,
        role=role,
        content=content,
        vector_id=vector_id,
        emotion_type=emotion_type,
        importance=importance,
        timestamp=timestamp or datetime.now()
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv.id

async def get_recent_conversations(
    db: AsyncSession,
    user_id: str,
    limit: int = 10
):
    """获取最近的对话（按时间从旧到新排序）"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.timestamp), desc(Conversation.id))
        .limit(limit)
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "role": c.role,
            "content": c.content,
            "timestamp": c.timestamp.isoformat(),
            "vector_id": c.vector_id,
            "emotion_type": c.emotion_type,
            "importance": c.importance
        }
        for c in reversed(conversations)
    ]


async def get_conversations_by_ids(
    db: AsyncSession,
    conversation_ids: List[int]
):
    """根据 ID 列表获取对话"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id.in_(conversation_ids))
        .order_by(Conversation.timestamp.asc())
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "role": c.role,
            "content": c.content,
            "timestamp": c.timestamp.isoformat(),
            "vector_id": c.vector_id,
            "emotion_type": c.emotion_type,
            "importance": c.importance
        }
        for c in conversations
    ]


async def update_conversation_vector_id(
    db: AsyncSession,
    conversation_id: int,
    vector_id: str
):
    """更新对话的 vector_id"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv:
        conv.vector_id = vector_id
        await db.commit()


# ========== 长期记忆索引 ==========

async def save_long_term_memory(
    db: AsyncSession,
    memory_type: str,
    key: str,
    value: str,
    keywords: str = "",
    file_path: str = "",
    importance: int = 1
):
    """
    写入长期记忆索引记录。
    value 存储内容摘要（前100字），便于快速预览，无需读文件。
    keywords 为逗号分隔的关键词字符串。
    file_path 为对应 .md 文件的相对路径。
    """
    memory = LongTermMemory(
        memory_type=memory_type,
        key=key,
        value=value[:100] if value else "",   # 仅存前100字作摘要
        keywords=keywords,
        file_path=file_path,
        importance=importance,
    )
    db.add(memory)
    await db.commit()

async def update_long_term_memory(
    db: AsyncSession,
    memory_type: str,
    key: str,
    new_value: str,
    new_keywords: str = "",
    importance: Optional[int] = None
) -> bool:
    """
    更新已有长期记忆索引记录的内容、关键词和重要度。
    返回 True 表示更新成功，False 表示未找到对应记录。
    """
    existing = await check_memory_exists(db, memory_type, key)
    if not existing:
        return False

    existing.value = new_value[:100] if new_value else ""
    existing.keywords = new_keywords
    if importance is not None:
        existing.importance = importance
    existing.updated_at = datetime.now()
    await db.commit()
    return True

async def save_or_update_long_term_memory(
    db: AsyncSession,
    memory_type: str,
    key: str,
    value: str,
    keywords: str = "",
    file_path: str = "",
    importance: int = 1,
    emotion_tag: str = "",
    emotional_intensity: int = 0
):
    """
    若记录已存在则更新，否则新建。
    这是写入长期记忆索引的统一入口。
    """
    existing = await check_memory_exists(db, memory_type, key)
    if existing:
        existing.value = value[:100] if value else ""
        existing.keywords = keywords
        existing.importance = importance
        existing.emotion_tag = emotion_tag
        existing.emotional_intensity = emotional_intensity
        existing.updated_at = datetime.now()
        await db.commit()
    else:
        memory = LongTermMemory(
            memory_type=memory_type,
            key=key,
            value=value[:100] if value else "",
            keywords=keywords,
            file_path=file_path,
            importance=importance,
            emotion_tag=emotion_tag,
            emotional_intensity=emotional_intensity
        )
        db.add(memory)
        await db.commit()

async def get_long_term_memories(
    db: AsyncSession,
    memory_type: str = None,
    limit: int = 20
) -> List[LongTermMemory]:
    """获取长期记忆索引，按重要度降序排列。"""
    query = select(LongTermMemory)
    if memory_type:
        query = query.where(LongTermMemory.memory_type == memory_type)
    query = query.order_by(desc(LongTermMemory.importance)).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

async def check_memory_exists(
    db: AsyncSession,
    memory_type: str,
    key: str
) -> Optional[LongTermMemory]:
    """
    检查长期记忆是否已存在（按 memory_type + key 唯一查找）。
    返回记录对象或 None。
    """
    result = await db.execute(
        select(LongTermMemory)
        .where(LongTermMemory.memory_type == memory_type)
        .where(LongTermMemory.key == key)
    )
    return result.scalar_one_or_none()


# ========== 用户状态 ==========

async def get_or_create_user_state(
    db: AsyncSession,
    user_id: str
):
    """获取或创建用户状态"""
    result = await db.execute(
        select(UserState).where(UserState.user_id == user_id)
    )
    state = result.scalar_one_or_none()

    if not state:
        state = UserState(user_id=user_id)
        db.add(state)
        await db.commit()
        await db.refresh(state)

    return state

async def update_user_state(
    db: AsyncSession,
    user_id: str,
    **kwargs
):
    """更新用户状态"""
    state = await get_or_create_user_state(db, user_id)
    for key, value in kwargs.items():
        setattr(state, key, value)
    state.last_interaction = datetime.now()
    await db.commit()

async def update_user_emotion(
    db: AsyncSession,
    user_id: str,
    emotion_type: str,
    mood: int,
    energy: int
):
    """更新用户情绪状态"""
    state = await get_or_create_user_state(db, user_id)
    state.emotion_type = emotion_type
    state.mood = mood
    state.energy_level = energy
    state.emotion_updated_at = datetime.now()
    state.last_interaction = datetime.now()
    await db.commit()

async def get_user_emotion(
    db: AsyncSession,
    user_id: str
) -> dict:
    """获取用户当前情绪状态"""
    state = await get_or_create_user_state(db, user_id)
    return {
        "emotion_type": state.emotion_type,
        "mood": state.mood,
        "energy": state.energy_level,
        "affinity": state.affinity,
        "last_interaction": state.last_interaction,
        "emotion_updated_at": state.emotion_updated_at
    }


# ========== 对话压缩相关 ==========

async def count_conversations(
    db: AsyncSession,
    user_id: str
) -> int:
    """统计用户的对话总数"""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user_id)
    )
    return result.scalar() or 0

async def get_oldest_conversations(
    db: AsyncSession,
    user_id: str,
    limit: int = 10
):
    """获取最旧的N条对话（按时间从旧到新排序）"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.timestamp.asc(), Conversation.id.asc())
        .limit(limit)
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "role": c.role,
            "content": c.content,
            "timestamp": c.timestamp.isoformat()
        }
        for c in conversations
    ]

async def delete_conversations_by_ids(
    db: AsyncSession,
    conversation_ids: list
):
    """删除指定ID的对话记录"""
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(Conversation)
        .where(Conversation.id.in_(conversation_ids))
    )
    await db.commit()
