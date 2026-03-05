import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from core.conversation import handle_message
from memory.short_term import get_recent, force_archive
from memory.long_term import save_memory, confirm_save_memory
from memory.rebuild_index import rebuild_all_indexes, find_unindexed_entries
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


class TTSSetReferAudioRequest(BaseModel):
    """预设参考音频（对应 GPT-SoVITS GET /set_refer_audio）"""
    refer_audio_path: str  # 服务器端绝对路径，3~10 秒音频


class TTSSwitchWeightsRequest(BaseModel):
    """热切换模型权重（对应 GPT-SoVITS GET /set_gpt_weights / /set_sovits_weights）"""
    weights_path: str  # .ckpt（GPT）或 .pth（SoVITS）的绝对/相对路径


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


@router.post("/memory/rebuild")
async def rebuild_memory_index():
    """
    重建记忆索引：
    扫描 memory_store/ 目录下的所有 .md 文件，
    将未建立数据库索引的记忆条目导入数据库。
    
    使用场景：
    - 迁移后自动重建索引
    - 手动编辑 .md 文件后重建索引
    - 数据库索引丢失后恢复
    """
    try:
        stats = await rebuild_all_indexes()
        return {
            "status": "ok",
            "msg": f"索引重建完成",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "msg": f"索引重建失败: {str(e)}"
        }


@router.get("/memory/unindexed")
async def get_unindexed_entries():
    """
    查找未建立索引的记忆条目
    返回文件中存在但数据库中不存在的记忆列表
    """
    try:
        unindexed = await find_unindexed_entries()
        return {
            "status": "ok",
            "count": len(unindexed),
            "entries": unindexed
        }
    except Exception as e:
        return {
            "status": "error",
            "msg": f"查询失败: {str(e)}"
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
    命中缓存时直接返回已有 URL，不重复请求 GPT-SoVITS API。
    """
    try:
        audio_url = await tts_adapter.synthesize(req.text)
        return {"audio_url": audio_url}
    except Exception as e:
        # 返回友好的错误信息，不暴露技术细节
        error_msg = "TTS 服务不可用"
        if "Connection" in str(e) or "connect" in str(e).lower():
            error_msg = "TTS 服务未启动"
        return {"audio_url": None, "error": error_msg}


@router.post("/tts/set_refer_audio")
async def tts_set_refer_audio(req: TTSSetReferAudioRequest):
    """
    预设参考音频路径（透传至 GPT-SoVITS GET /set_refer_audio）。
    设置成功后，后续 TTS 合成请求无需重复传递 ref_audio_path。

    注意：
      - refer_audio_path 必须是 GPT-SoVITS 服务器端可访问的绝对路径
      - 参考音频时长须为 3~10 秒
    """
    success = await tts_adapter.set_refer_audio(req.refer_audio_path)
    if success:
        return {"status": "ok", "msg": f"参考音频已预设：{req.refer_audio_path}"}
    return {"status": "error", "msg": "预设参考音频失败，请检查服务是否运行及路径是否正确"}


@router.post("/tts/set_gpt_weights")
async def tts_set_gpt_weights(req: TTSSwitchWeightsRequest):
    """
    热切换 GPT 模型权重（透传至 GPT-SoVITS GET /set_gpt_weights）。
    无需重启服务，直接切换为其他角色的 GPT 模型（.ckpt 文件）。
    """
    success = await tts_adapter.switch_gpt_weights(req.weights_path)
    if success:
        return {"status": "ok", "msg": f"GPT 模型已切换：{req.weights_path}"}
    return {"status": "error", "msg": "GPT 模型切换失败，请检查服务是否运行及路径是否正确"}


@router.post("/tts/set_sovits_weights")
async def tts_set_sovits_weights(req: TTSSwitchWeightsRequest):
    """
    热切换 SoVITS 模型权重（透传至 GPT-SoVITS GET /set_sovits_weights）。
    无需重启服务，直接切换为其他角色的 SoVITS 模型（.pth 文件）。
    """
    success = await tts_adapter.switch_sovits_weights(req.weights_path)
    if success:
        return {"status": "ok", "msg": f"SoVITS 模型已切换：{req.weights_path}"}
    return {"status": "error", "msg": "SoVITS 模型切换失败，请检查服务是否运行及路径是否正确"}


@router.post("/chat")
async def chat(req: ChatRequest):
    # 1. LLM 生成回复（已包含情绪计算）
    result = await handle_message(req.user_id, req.message)
    reply  = result["reply"]
    emotion = result["emotion"]  # 新增

    # 2. 并发调用 TTS（不阻塞主流程，失败时静默降级）
    audio_url = None
    if reply:
        try:
            audio_url = await tts_adapter.synthesize(reply)
        except Exception as e:
            # TTS 失败不影响对话功能，仅记录日志
            print(f"⚠️  [TTS] 音频生成失败（不影响对话）：{e}")
            audio_url = None

    return {
        "reply":       reply,
        "memory_info": result["memory_info"],
        "audio_url":   audio_url,   # "/audio/xxxx.wav" 或 null
        "emotion":     emotion       # 新增返回
    }
