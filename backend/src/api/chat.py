import asyncio
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from core.conversation import handle_message
from memory.short_term import get_recent, export_memories, import_memories
from memory.long_term import save_memory, confirm_save_memory
from memory.compression import compress_conversations, CompressionError
from memory.vector_store import add_conversation_vector
from tts import tts_adapter
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from db.database import AsyncSessionLocal
from db.crud import (
    get_recent_conversations,
    count_conversations,
    save_conversation,
    delete_conversations_by_ids,
    update_conversation_vector_id
)

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


class MemoryImportRequest(BaseModel):
    user_id: str = "依洛沐"
    rebuild_vectors: bool = True
    skip_existing: bool = True


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
async def archive_memory(user_id: str = "依洛沐", role: str = "default"):
    """
    归档短期记忆为长期记忆
    
    流程：
    1. 查询所有短期记忆
    2. 使用LLM压缩总结
    3. 保存为长期记忆
    4. 生成向量索引
    5. 清空短期记忆
    
    参数：
    - user_id: 用户ID
    - role: 角色类型（用于过滤）
    
    返回：
    - success: 是否成功
    - message: 提示消息
    - data: 归档结果数据
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. 查询所有短期记忆
            conversations = await get_recent_conversations(db, user_id, limit=10000)
            
            if not conversations:
                return {
                    "success": False,
                    "message": "没有可归档的对话",
                    "error_code": "NO_CONVERSATIONS"
                }
            
            print(f"🔄 [archive] 开始归档 {len(conversations)} 条对话...")
            
            # 2. 使用LLM压缩总结
            try:
                summary = await compress_conversations(conversations, user_id, role)
            except CompressionError as e:
                print(f"❌ [archive] 压缩失败: {e}")
                return {
                    "success": False,
                    "message": f"压缩失败：{str(e)}",
                    "error_code": "LLM_ERROR"
                }
            
            # 3. 保存为长期记忆
            try:
                memory_type = "conversation_summary"
                key = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 保存长期记忆（使用confirm_save_memory会自动生成向量）
                memory_info = {
                    "memory_type": memory_type,
                    "key": key,
                    "value": summary,
                    "importance": 4
                }
                
                success = await confirm_save_memory(user_id, memory_info)
                
                if not success:
                    raise Exception("保存长期记忆失败")
                
                print(f"✅ [archive] 长期记忆已保存: {key}")
                
            except Exception as e:
                print(f"❌ [archive] 保存长期记忆失败: {e}")
                return {
                    "success": False,
                    "message": f"保存失败：{str(e)}",
                    "error_code": "DB_ERROR"
                }
            
            # 4. 清空短期记忆
            try:
                conversation_ids = [c["id"] for c in conversations]
                await delete_conversations_by_ids(db, conversation_ids)
                print(f"✅ [archive] 已清空 {len(conversation_ids)} 条短期记忆")
            except Exception as e:
                print(f"❌ [archive] 清空短期记忆失败: {e}")
                # 不返回错误，因为长期记忆已保存
            
            return {
                "success": True,
                "message": f"已归档 {len(conversations)} 条对话",
                "data": {
                    "archived_count": len(conversations),
                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                    "memory_type": memory_type,
                    "key": key
                }
            }
            
        except Exception as e:
            print(f"❌ [archive] 归档失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"归档失败：{str(e)}",
                "error_code": "UNKNOWN_ERROR"
            }


@router.post("/memory/export")
async def export_memory(user_id: str = "依洛沐"):
    """
    导出用户的所有记忆数据（用于备份或迁移）
    
    导出内容：
    - MySQL 中的所有对话记录（包含情绪、重要度等元数据）
    - 导出时间戳和统计信息
    
    注意：
    - Qdrant 向量数据不导出（可以从 MySQL 重建）
    - memory_store/*.md 文件需要手动备份
    
    返回：JSON 文件下载
    """
    result = await export_memories(user_id)
    
    if result["success"]:
        file_path = result["file_path"]
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/json"
        )
    else:
        return {
            "status": "error",
            "msg": result["msg"]
        }


@router.post("/memory/import")
async def import_memory(
    file: UploadFile = File(...),
    user_id: str = "依洛沐",
    rebuild_vectors: bool = True,
    skip_existing: bool = True
):
    """
    导入记忆数据（用于迁移或恢复）
    
    导入流程：
    1. 上传之前导出的 JSON 文件
    2. 将对话记录导入 MySQL
    3. 可选：重建 Qdrant 向量索引
    
    参数：
    - file: 导出的 JSON 文件
    - user_id: 用户 ID
    - rebuild_vectors: 是否重建向量索引（默认 True）
    - skip_existing: 是否跳过已存在的记录（默认 True）
    """
    # 保存上传的文件到临时目录
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / file.filename
    
    try:
        with open(temp_file, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # 执行导入
        result = await import_memories(
            user_id=user_id,
            import_path=str(temp_file),
            rebuild_vectors=rebuild_vectors,
            skip_existing=skip_existing
        )
        
        if result["success"]:
            return {
                "status": "ok",
                "msg": result["msg"],
                "imported_count": result["imported_count"],
                "skipped_count": result["skipped_count"],
                "vector_count": result.get("vector_count", 0)
            }
        else:
            return {
                "status": "error",
                "msg": result["msg"]
            }
    
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"⚠️  清理临时文件失败: {e}")


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
