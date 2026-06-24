import asyncio
from fastapi import APIRouter, Depends, HTTPException
from api.deps import verify_token
from pydantic import BaseModel
from core.conversation import handle_message
from memory.short_term import get_recent
from tts import tts_adapter
from typing import Optional, Dict, Any

from db.database import AsyncSessionLocal
from db.crud import (
    count_conversations,
    delete_conversation_by_id,
)
from config import SHORT_TERM_MAX

router = APIRouter(dependencies=[Depends(verify_token)])


class ChatRequest(BaseModel):
    user_id: str = "依洛沐"
    message: str


@router.get("/history")
async def get_history(user_id: str = "依洛沐", limit: int = 50):
    return await get_recent(user_id, limit=limit)


@router.delete("/chat/message/{id}")
async def delete_chat_message(id: int, user_id: str = "依洛沐"):
    """
    删除单条聊天消息：
    1. 从 MySQL 中删除记录
    2. 从 FAISS 向量数据库中删除对应的向量
    """
    async with AsyncSessionLocal() as db:
        success = await delete_conversation_by_id(db, id)
        if not success:
            raise HTTPException(status_code=404, detail="未找到该聊天记录")

    # 从向量库删除
    from memory.vector_store import delete_conversation_vector
    delete_conversation_vector(user_id, id)

    return {"status": "ok", "msg": "消息已删除"}


async def _auto_archive_if_needed(user_id: str):
    """
    当短期记忆条数 ≥ SHORT_TERM_MAX 时，自动触发归档。
    作为异步任务运行，不阻塞 /chat 主流程。
    """
    try:
        async with AsyncSessionLocal() as db:
            total = await count_conversations(db, user_id)
        if total >= SHORT_TERM_MAX:
            print(
                f"🔔 [auto-archive] 对话数 {total} ≥ 阈值 {SHORT_TERM_MAX}，触发自动归档..."
            )
            from api.memory import _do_archive
            await _do_archive(user_id)
    except Exception as e:
        print(f"⚠️  [auto-archive] 自动归档失败（不影响对话）: {e}")


@router.post("/chat")
async def chat(req: ChatRequest):
    # 1. LLM 生成回复（已包含情绪计算、生成 user_conv_id 和 assistant_conv_id）
    result = await handle_message(req.user_id, req.message)
    reply  = result["reply"]
    emotion = result["emotion"]

    # 2. 并发调用 TTS（不阻塞主流程，失败时静默降级）
    audio_url = None
    if reply:
        try:
            audio_url = await tts_adapter.synthesize(reply)
        except Exception as e:
            # TTS 失败不影响对话功能，仅记录日志
            print(f"⚠️  [TTS] 音频生成失败（不影响对话）：{e}")
            audio_url = None

    # 3. 异步检查短期记忆条数，达到阈值时自动归档（不阻塞当前请求）
    asyncio.create_task(_auto_archive_if_needed(req.user_id))

    return {
        "reply":       reply,
        "memory_info": result["memory_info"],
        "audio_url":   audio_url,   # "/audio/xxxx.wav" 或 null
        "emotion":     emotion,
        "user_conv_id": result.get("user_conv_id"),
        "assistant_conv_id": result.get("assistant_conv_id"),
    }
