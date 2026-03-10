import asyncio
import random
from memory.recall import recall_context
from memory.vector_store import add_conversation_vector
from core.person import build_person
from core.prompt import build_prompt
from core.emotion import update_emotion_state, detect_sensitive_topics
from llm.adapter import generate
from memory.long_term import check_memory_trigger
from db.database import get_db_session, AsyncSessionLocal
from db.crud import get_user_emotion, save_conversation, update_conversation_vector_id
from datetime import datetime
from typing import Dict, Any


def calculate_response_delay(message: str, emotion_state: dict) -> float:
    """
    计算响应延迟时间（秒）
    
    因素：
    - 消息长度
    - 情绪类型
    - 敏感话题
    """
    # 基础延迟：根据消息长度
    base_delay = 0.5
    if len(message) > 100:
        base_delay = 2.0
    elif len(message) > 50:
        base_delay = 1.2
    
    # 情绪延迟
    emotion_type = emotion_state.get("emotion_type", "calm")
    if emotion_type in ["melancholy", "guarded"]:
        base_delay += 0.8  # 沉默、警戒时反应慢
    elif emotion_type == "nostalgic":
        base_delay += 0.5  # 回忆时稍慢
    
    # 敏感话题延迟
    sensitive = detect_sensitive_topics(message)
    if "trauma" in sensitive.get("topics", []):
        base_delay += 1.0  # 触及创伤，犹豫更久
    
    # 添加随机波动 ±20%
    delay = base_delay * random.uniform(0.8, 1.2)
    return min(delay, 3.5)  # 最长不超过 3.5 秒


async def check_greeting(user_id: str) -> str:
    """
    检查是否需要主动问候
    
    规则：
    - 间隔 > 6小时：简单问候
    - 间隔 > 3天：带想念感的问候
    """
    async with get_db_session() as db:
        state = await get_user_emotion(db, user_id)
        last_interaction = state["last_interaction"]
        
        now = datetime.now()
        time_gap_hours = (now - last_interaction).total_seconds() / 3600
        
        if time_gap_hours > 72:  # > 3天
            greetings = [
                "好久不见了...",
                "已经...过了这么久了吗。",
                "你还记得我吗..."
            ]
            return random.choice(greetings) + "\n\n"
        elif time_gap_hours > 6:  # > 6小时
            greetings = [
                "已经...过了一段时间了呢。",
                "嗯...你来了。"
            ]
            return random.choice(greetings) + "\n\n"
        
        return ""


async def handle_message(user_id: str, message: str) -> Dict[str, Any]:
    """处理消息并返回回复和情绪信息"""
    
    # 1. 更新情绪状态
    emotion_state = await update_emotion_state(user_id, message)
    
    # 2. 响应延迟（模拟思考）
    delay = calculate_response_delay(message, emotion_state)
    await asyncio.sleep(delay)
    
    # 3. 检查是否需要主动问候
    greeting = await check_greeting(user_id)
    
    # 4. 回忆上下文（传入当前消息用于向量检索）
    context = await recall_context(user_id, current_message=message)
    
    # 5. 人格
    person = build_person(user_id)
    
    # 6. 构建提示词（传入情绪状态）
    prompt = build_prompt(
        person=person,
        memory=context,
        user_message=message,
        emotion_type=emotion_state["emotion_type"],
        mood=emotion_state["mood"],
        energy=emotion_state["energy"]
    )
    
    # 7. 生成回复
    reply = await generate(prompt)
    
    # 8. 如果有问候，拼接在前面
    if greeting:
        reply = greeting + reply
    
    # 9. 保存到数据库并生成向量
    async with AsyncSessionLocal() as db:
        # 保存用户消息
        user_conv_id = await save_conversation(
            db, user_id, "user", message,
            emotion_type=emotion_state["emotion_type"],
            importance=3  # 默认重要度
        )
        
        # 保存助手回复
        assistant_conv_id = await save_conversation(
            db, user_id, "sakura", reply,
            emotion_type=emotion_state["emotion_type"],
            importance=3
        )
    
    # 10. 异步生成向量（不阻塞主流程）
    asyncio.create_task(_add_vectors_async(
        user_id, user_conv_id, message, assistant_conv_id, reply, emotion_state
    ))
    
    # 11. 检查长期记忆触发
    memory_info = await check_memory_trigger(user_id, message)
    
    return {
        "reply": reply,
        "memory_info": memory_info,
        "emotion": emotion_state
    }


async def _add_vectors_async(
    user_id: str,
    user_conv_id: int,
    user_message: str,
    assistant_conv_id: int,
    assistant_reply: str,
    emotion_state: dict
):
    """异步添加向量（不阻塞主流程）"""
    try:
        # 为用户消息生成向量
        user_vector_id = await add_conversation_vector(
            user_id=user_id,
            conversation_id=user_conv_id,
            role="user",
            content=user_message,
            emotion_type=emotion_state["emotion_type"],
            importance=3
        )
        
        # 为助手回复生成向量
        assistant_vector_id = await add_conversation_vector(
            user_id=user_id,
            conversation_id=assistant_conv_id,
            role="sakura",
            content=assistant_reply,
            emotion_type=emotion_state["emotion_type"],
            importance=3
        )
        
        # 更新数据库中的 vector_id
        async with AsyncSessionLocal() as db:
            if user_vector_id:
                await update_conversation_vector_id(db, user_conv_id, user_vector_id)
            if assistant_vector_id:
                await update_conversation_vector_id(db, assistant_conv_id, assistant_vector_id)
        
        print(f"✅ 向量已生成: user={user_vector_id}, assistant={assistant_vector_id}")
        
    except Exception as e:
        print(f"❌ 向量生成失败: {e}")
        # 向量生成失败不影响主流程，对话已保存在数据库中
