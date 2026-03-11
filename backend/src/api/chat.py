import asyncio
from fastapi import APIRouter, Depends, UploadFile, File
from api.deps import verify_token
from fastapi.responses import FileResponse
from pydantic import BaseModel
from core.conversation import handle_message
from memory.short_term import get_recent, export_memories, import_memories
from memory.long_term import save_memory, confirm_save_memory
from memory.keyword_extractor import extract_keywords_batch, keywords_to_str
from memory import file_store
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
    update_conversation_vector_id,
    get_oldest_conversations,
    bulk_save_archived_conversations,
)
from config import SHORT_TERM_MAX, SHORT_TERM_ARCHIVE_COUNT

router = APIRouter(dependencies=[Depends(verify_token)])


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
async def get_history(user_id: str = "依洛沐", limit: int = 50):
    return await get_recent(user_id, limit=limit)


@router.post("/memory/archive")
async def archive_memory(user_id: str = "依洛沐", role: str = "default"):
    """
    将最早的 SHORT_TERM_ARCHIVE_COUNT 条短期记忆归档为长期记忆。

    流程：
    1. 取最旧的 N 条对话记录
    2. 一次性批量提取关键词（分批 LLM 请求， ~5次而非 150次）
    3. 将每条对话原文写入 archived_N.md 文件
    4. 批量写入 MySQL long_term_memory 表（保留完整原文）
    5. 从 MySQL conversations 表删除已归档记录（FAISS 向量保留）

    参数：
    - user_id: 用户ID
    - role: 角色类型（保留兼容）
    """
    result = await _do_archive(user_id)
    return result


async def _do_archive(user_id: str) -> dict:
    """
    归档核心逻辑（可被手动接口和自动触发共用）。
    """
    async with AsyncSessionLocal() as db:
        # 1. 查询当前总条数
        total = await count_conversations(db, user_id)
        if total == 0:
            return {
                "success": False,
                "message": "没有可归档的对话",
                "error_code": "NO_CONVERSATIONS"
            }

        # 2. 取最旧的 N 条对话
        conversations = await get_oldest_conversations(
            db, user_id, limit=SHORT_TERM_ARCHIVE_COUNT
        )
        if not conversations:
            return {
                "success": False,
                "message": "没有可归档的对话",
                "error_code": "NO_CONVERSATIONS"
            }

        print(f"🔄 [archive] 开始归档最早 {len(conversations)} 条（共 {total} 条）...")

    # 3. 批量提取关键词（单次 LLM 批量请求）
    # 内容格式："[timestamp] role: content"
    contents = [
        f"[{conv['timestamp']}] {conv['role']}: {conv['content']}"
        for conv in conversations
    ]
    print(f"🔄 [archive] 批量提取关键词（{len(contents)}条, 每批最多30条）...")
    all_keywords = await extract_keywords_batch(contents)

    # 4. 逐条写入 archived_N.md 文件
    db_records = []       # 待写入数据库的条目
    archived_ids = []     # MySQL 待删除的对话 ID
    file_errors = 0

    for i, conv in enumerate(conversations):
        keywords = all_keywords[i] if i < len(all_keywords) else []
        kw_str = keywords_to_str(keywords)
        key = f"conv_{conv['id']}_{conv['timestamp'][:10]}"
        value = f"[{conv['timestamp']}] {conv['role']}: {conv['content']}"
        emotion_type = conv.get("emotion_type", "calm")
        importance = conv.get("importance", 3)

        # 写入 .md 文件
        try:
            file_path = await file_store.write_entry(
                memory_type="archived_conversation",
                key=key,
                content=conv["content"],
                keywords=keywords,
                importance=importance,
                role=conv["role"],
                emotion_type=emotion_type,
                timestamp=conv["timestamp"],
            )
        except Exception as e:
            print(f"⚠️  [archive] 文件写入失败 conv_id={conv['id']}: {e}")
            file_path = ""
            file_errors += 1

        # 收集 DB 写入条目
        db_records.append({
            "key": key,
            "value": value,          # 完整原文，不截断
            "keywords": kw_str,
            "file_path": file_path,
            "emotion_tag": emotion_type,
            "emotional_intensity": max(0, importance - 1),
            "importance": importance,
        })
        archived_ids.append(conv["id"])

    # 5. 批量写入数据库（单次事务）
    async with AsyncSessionLocal() as db:
        try:
            inserted = await bulk_save_archived_conversations(db, db_records)
            print(f"✅ [archive] 已写入数据库 {inserted} 条长期记忆")
        except Exception as e:
            print(f"❌ [archive] 数据库写入失败: {e}")
            return {
                "success": False,
                "message": f"数据库写入失败：{str(e)}",
                "error_code": "DB_ERROR"
            }

        # 6. 从 MySQL conversations 表删除已归档的对话记录
        #    FAISS 向量不删除，RAG 检索不受影响
        try:
            await delete_conversations_by_ids(db, archived_ids)
            print(f"✅ [archive] 已从 conversations 表删除 {len(archived_ids)} 条（FAISS 向量保留）")
        except Exception as e:
            print(f"⚠️  [archive] 删除 conversations 失败: {e}")
            # 删除失败不回滚，长期记忆已成功写入

    remaining = total - len(archived_ids)
    print(
        f"✅ [archive] 归档完成: 共归档 {len(archived_ids)} 条, "
        f"文件失败 {file_errors} 条, 剩余对话 {remaining} 条"
    )

    return {
        "success": True,
        "message": f"已归档 {len(archived_ids)} 条对话（剩余 {remaining} 条）",
        "data": {
            "archived_count": len(archived_ids),
            "file_errors": file_errors,
            "remaining": remaining,
        }
    }


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
            await _do_archive(user_id)
    except Exception as e:
        print(f"⚠️  [auto-archive] 自动归档失败（不影响对话）: {e}")


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

    # 3. 异步检查短期记忆条数，达到阈值时自动归档（不阻塞当前请求）
    asyncio.create_task(_auto_archive_if_needed(req.user_id))

    return {
        "reply":       reply,
        "memory_info": result["memory_info"],
        "audio_url":   audio_url,   # "/audio/xxxx.wav" 或 null
        "emotion":     emotion       # 新增返回
    }
