import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from core.conversation import handle_message
from memory.short_term import get_recent, force_archive
from memory.long_term import save_memory, confirm_save_memory
from tts import tts_adapter
from typing import Optional, Dict, Any

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str = "依洛沐"
    message: str


class MemoryRequest(BaseModel):
    user_id: str = "依洛沐"
    content: str


class MemoryConfirmRequest(BaseModel):
    user_id: str = "依洛沐"
    memory_info: Dict[str, Any]
    confirmed: bool


class TTSRequest(BaseModel):
    text: str


@router.get("/history")
async def get_history(user_id: str = "依洛沐"):
    return await get_recent(user_id)


@router.post("/memory/archive")
async def archive_memory(user_id: str = "依洛沐"):
    """
    手动触发短期记忆归档：
    将当前全部短期记忆压缩总结后写入长期记忆文件和数据库索引，
    然后清空数据库中的短期对话记录。
    不受对话数量阈值限制，随时可手动触发。
    """
    result = await force_archive(user_id)
    if result["success"]:
        return {
            "status": "ok",
            "msg": result["msg"],
            "archived_count": result.get("archived_count", 0)
        }
    else:
        return {
            "status": "error",
            "msg": result["msg"]
        }


@router.post("/memory")
async def add_memory(req: MemoryRequest):
    await save_memory(req.user_id, req.content)
    return {"status": "ok", "msg": "记忆已保存"}


@router.post("/memory/confirm")
async def confirm_memory(req: MemoryConfirmRequest):
    """确认保存记忆"""
    if req.confirmed:
        success = await confirm_save_memory(req.user_id, req.memory_info)
        if success:
            return {
                "status": "ok",
                "msg": "记忆已保存"
            }
    else:
        return {
            "status": "cancelled",
            "msg": "已取消保存"
        }

    return {"status": "error", "msg": "保存失败"}


@router.post("/tts")
async def generate_tts(req: TTSRequest):
    """
    按需生成 TTS 音频。
    前端手动点击播放按钮且尚未生成过音频时调用。
    命中缓存时直接返回已有 URL，不重复请求 Fish Audio API。
    """
    audio_url = await tts_adapter.synthesize(req.text)
    return {"audio_url": audio_url}


@router.post("/chat")
async def chat(req: ChatRequest):
    # 1. LLM 生成回复
    result = await handle_message(req.user_id, req.message)
    reply  = result["reply"]

    # 2. 并发调用 TTS（不阻塞主流程，失败时静默降级）
    audio_url = await tts_adapter.synthesize(reply) if reply else None

    return {
        "reply":       reply,
        "memory_info": result["memory_info"],
        "audio_url":   audio_url,   # "/audio/xxxx.mp3" 或 null
    }
