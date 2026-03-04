from fastapi import APIRouter
from pydantic import BaseModel
from core.conversation import handle_message
from memory.short_term import get_recent, force_archive
from memory.long_term import save_memory, confirm_save_memory
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
        # 用户取消保存
        return {
            "status": "cancelled",
            "msg": "已取消保存"
        }
    
    return {"status": "error", "msg": "保存失败"}

@router.post("/chat")
async def chat(req: ChatRequest):
    result = await handle_message(req.user_id, req.message)
    
    # 始终返回模型回复，同时附带记忆信息（如果有）
    return {
        "reply": result["reply"],
        "memory_info": result["memory_info"]
    }
