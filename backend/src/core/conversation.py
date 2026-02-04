
from memory.recall import recall_context
from core.person import build_person
from core.prompt import build_prompt
from llm.adapter import generate
from memory.short_term import save_turn
from memory.long_term import check_memory_trigger
from typing import Dict, Any

async def handle_message(user_id: str, message: str) -> Dict[str, Any]:
    """处理消息并返回回复和可能的记忆信息"""
    
    # 正常对话流程
    # 回忆
    context = await recall_context(user_id)
    # 人格
    person = build_person(user_id)
    # 构建提示词
    prompt = build_prompt(person=person, memory=context, user_message=message)
    # 生成回复
    reply = await generate(prompt)
    # 保存到短时记忆
    await save_turn(user_id, message, reply)
    
    # 检查是否需要保存长期记忆（不影响回复）
    memory_info = await check_memory_trigger(user_id, message)
    
    return {
        "reply": reply,
        "memory_info": memory_info
    }
