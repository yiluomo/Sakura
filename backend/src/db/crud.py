from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Conversation, LongTermMemory, UserState
from datetime import datetime

# ========== 对话历史 ==========

async def save_conversation(
    db: AsyncSession,
    user_id: str,
    role: str,
    content: str
):
    """保存一条对话"""
    conv = Conversation(user_id=user_id, role=role, content=content)
    db.add(conv)
    await db.commit()

async def get_recent_conversations(
    db: AsyncSession,
    user_id: str,
    limit: int = 10
):
    """获取最近的对话（按时间从旧到新排序）"""
    # 先降序获取最近的N条记录（按timestamp和id排序）
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.timestamp), desc(Conversation.id))
        .limit(limit)
    )
    conversations = result.scalars().all()
    # 反转顺序，使其从旧到新
    return [
        {"role": c.role, "content": c.content, "timestamp": c.timestamp.isoformat()}
        for c in reversed(conversations)
    ]

# ========== 长期记忆 ==========

async def save_long_term_memory(
    db: AsyncSession,
    user_id: str,
    memory_type: str,
    key: str,
    value: str,
    importance: int = 1
):
    """保存长期记忆"""
    memory = LongTermMemory(
        user_id=user_id,
        memory_type=memory_type,
        key=key,
        value=value,
        importance=importance
    )
    db.add(memory)
    await db.commit()

async def get_long_term_memories(
    db: AsyncSession,
    user_id: str,
    memory_type: str = None
):
    """获取长期记忆"""
    query = select(LongTermMemory).where(LongTermMemory.user_id == user_id)
    if memory_type:
        query = query.where(LongTermMemory.memory_type == memory_type)
    
    result = await db.execute(query.order_by(desc(LongTermMemory.importance)))
    return result.scalars().all()

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

   #记忆去重
async def check_memory_exists(
    db: AsyncSession,
    user_id: str,
    memory_type: str,
    key: str
):
    """检查记忆是否已存在"""
    result = await db.execute(
        select(LongTermMemory)
        .where(LongTermMemory.user_id == user_id)
        .where(LongTermMemory.memory_type == memory_type)
        .where(LongTermMemory.key == key)
    )
    return result.scalar_one_or_none()

