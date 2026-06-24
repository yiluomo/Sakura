import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from api.deps import verify_token
from fastapi.responses import FileResponse
from pydantic import BaseModel
from memory.short_term import export_memories, import_memories
from memory.long_term import save_memory, confirm_save_memory, delete_long_term_memory_full
from memory.keyword_extractor import extract_keywords_batch, keywords_to_str, extract_keywords
from memory import file_store
from memory.vector_store import add_conversation_vector, delete_conversation_vector
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from db.database import AsyncSessionLocal
from db.crud import (
    count_conversations,
    delete_conversations_by_ids,
    get_oldest_conversations,
    bulk_save_archived_conversations,
    get_long_term_memories,
    save_or_update_long_term_memory,
    check_memory_exists,
    update_long_term_memory_vector_id,
)
from config import SHORT_TERM_MAX, SHORT_TERM_ARCHIVE_COUNT

router = APIRouter(dependencies=[Depends(verify_token)])


class MemoryRequest(BaseModel):
    user_id: str = "依洛沐"
    content: str


class MemoryConfirmRequest(BaseModel):
    user_id: str = "依洛沐"
    memory_info: Dict[str, Any]
    confirmed: bool


class MemoryCreateRequest(BaseModel):
    content: str
    category: str
    keywords: Optional[List[str]] = None
    importance: Optional[int] = 3


class MemoryUpdateRequest(BaseModel):
    content: str
    category: str
    keywords: Optional[List[str]] = None
    importance: Optional[int] = 3


@router.get("/memory")
async def list_memories():
    """获取所有长期记忆"""
    async with AsyncSessionLocal() as db:
        memories = await get_long_term_memories(db, limit=100000)
        
        result = []
        for m in memories:
            kw_list = [k.strip() for k in m.keywords.split(",") if k.strip()] if m.keywords else []
            result.append({
                "id": str(m.id),
                "content": m.value,  # m.value 现已完整保存
                "category": m.memory_type,
                "keywords": kw_list,
                "createdAt": m.created_at.isoformat() if m.created_at else None,
                "updatedAt": m.updated_at.isoformat() if m.updated_at else None,
            })
        return result


@router.post("/memory/create_direct")
async def create_memory_direct(req: MemoryCreateRequest, user_id: str = "依洛沐"):
    """
    前端记忆管理页面手动添加记忆的 API。
    """
    category = req.category
    content = req.content
    importance = req.importance or 3
    
    # 生成唯一 key 防止覆盖
    key = f"manual_{int(datetime.now().timestamp())}"
    
    # 提取关键词
    keywords = req.keywords
    if not keywords:
        keywords = await extract_keywords(content)
    kw_str = keywords_to_str(keywords)
    
    # 写入文件
    rel_path = await file_store.write_entry(category, key, content, keywords, importance)
    
    # 写入数据库 (full_value=True 保持完整内容)
    async with AsyncSessionLocal() as db:
        await save_or_update_long_term_memory(
            db, category, key, content, kw_str, rel_path, importance, full_value=True
        )
        
        # 获取刚刚插入的记录以拿到 ID
        inserted = await check_memory_exists(db, category, key)
        if not inserted:
            raise HTTPException(status_code=500, detail="保存记忆失败")
            
        memory_id = inserted.id

    # 写入 FAISS 向量库
    vector_id = ""
    try:
        vector_id = await add_conversation_vector(
            user_id=user_id,
            conversation_id=memory_id,
            role="long_term_memory",
            content=content,
            emotion_type="calm",
            importance=importance
        )
        if vector_id:
            async with AsyncSessionLocal() as db:
                await update_long_term_memory_vector_id(db, memory_id, vector_id)
    except Exception as e:
        print(f"⚠️  手动创建长期记忆向量生成失败: {e}")

    # 构造并返回前端所需格式
    async with AsyncSessionLocal() as db:
        inserted = await check_memory_exists(db, category, key)
        return {
            "id": str(inserted.id),
            "content": inserted.value,
            "category": inserted.memory_type,
            "keywords": keywords,
            "createdAt": inserted.created_at.isoformat() if inserted.created_at else None,
            "updatedAt": inserted.updated_at.isoformat() if inserted.updated_at else None,
        }


@router.put("/memory/{id}")
async def update_memory_by_id(id: int, req: MemoryUpdateRequest, user_id: str = "依洛沐"):
    """
    前端记忆管理页面编辑更新记忆的 API。
    """
    async with AsyncSessionLocal() as db:
        from db.models import LongTermMemory
        from sqlalchemy import select
        
        result = await db.execute(select(LongTermMemory).where(LongTermMemory.id == id))
        memory = result.scalar_one_or_none()
        if not memory:
            raise HTTPException(status_code=404, detail="未找到该记忆记录")
            
        old_category = memory.memory_type
        key = memory.key
        
    category = req.category
    content = req.content
    importance = req.importance or 3
    
    # 提取关键词
    keywords = req.keywords
    if not keywords:
        keywords = await extract_keywords(content)
    kw_str = keywords_to_str(keywords)
    
    # 如果分类变了，需要先删除旧文件中的条目，再写入新文件
    if old_category != category:
        await file_store.delete_entry(old_category, key)
        
    rel_path = await file_store.write_entry(category, key, content, keywords, importance)
    
    async with AsyncSessionLocal() as db:
        await save_or_update_long_term_memory(
            db, category, key, content, kw_str, rel_path, importance, full_value=True
        )
        
    # 更新向量数据库
    try:
        delete_conversation_vector(user_id, id)
        vector_id = await add_conversation_vector(
            user_id=user_id,
            conversation_id=id,
            role="long_term_memory",
            content=content,
            emotion_type="calm",
            importance=importance
        )
        if vector_id:
            async with AsyncSessionLocal() as db:
                await update_long_term_memory_vector_id(db, id, vector_id)
    except Exception as e:
        print(f"⚠️  更新长期记忆向量失败: {e}")
        
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(LongTermMemory).where(LongTermMemory.id == id))
        updated = result.scalar_one_or_none()
        return {
            "id": str(updated.id),
            "content": updated.value,
            "category": updated.memory_type,
            "keywords": keywords,
            "createdAt": updated.created_at.isoformat() if updated.created_at else None,
            "updatedAt": updated.updated_at.isoformat() if updated.updated_at else None,
        }


@router.delete("/memory/{id}")
async def delete_memory_by_id(id: int, user_id: str = "依洛沐"):
    """
    前端记忆管理页面删除记忆的 API。
    """
    success = await delete_long_term_memory_full(user_id, id)
    if success:
        return {"status": "ok", "msg": "记忆已删除"}
    raise HTTPException(status_code=404, detail="未找到该记忆或删除失败")


@router.post("/memory/archive")
async def archive_memory(user_id: str = "依洛沐", role: str = "default"):
    """
    将最早的 SHORT_TERM_ARCHIVE_COUNT 条短期记忆归档为长期记忆。
    """
    result = await _do_archive(user_id)
    return result


async def _do_archive(user_id: str) -> dict:
    """
    归档核心逻辑（将短期记忆聚合、总结并按倒序保存为一条长期记忆）。
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

    # 3. 对话内容总结（使用已有的 compression 模块）
    from memory.compression import compress_conversations
    try:
        summary = await compress_conversations(conversations, user_id)
    except Exception as e:
        print(f"⚠️  [archive] 对话总结失败: {e}，将使用降级策略")
        # 降级直接拼接对话
        summary = "（对话总结生成失败）"

    # 4. 提取总结的关键词
    keywords = await extract_keywords(summary)
    kw_str = keywords_to_str(keywords)

    # 5. 按照发生时间倒序排列对话详情，并与总结文本合并
    conversations_reverse = list(reversed(conversations))
    dialogues_text_list = []
    for conv in conversations_reverse:
        ts_clean = conv["timestamp"].replace("T", " ")
        role_label = "用户" if conv["role"] == "user" else "樱"
        dialogues_text_list.append(f"[{ts_clean}] {role_label}: {conv['content']}")
    dialogues_text = "\n".join(dialogues_text_list)

    combined_content = f"【对话总结】\n{summary}\n\n【对话详情（倒序）】\n{dialogues_text}"

    # 6. 生成唯一会话 key
    start_ts = conversations[0]["timestamp"].replace("T", "_").replace(":", "-")[:19]
    end_ts = conversations[-1]["timestamp"].replace("T", "_").replace(":", "-")[:19]
    key = f"archive_{start_ts}_to_{end_ts}"

    # 7. 写入 .md 文件
    file_errors = 0
    try:
        file_path = await file_store.write_entry(
            memory_type="archived_conversation",
            key=key,
            content=combined_content,
            keywords=keywords,
            importance=3,
            role="session",
            emotion_type="calm",
            timestamp=f"{conversations[0]['timestamp']} 至 {conversations[-1]['timestamp']}",
        )
    except Exception as e:
        print(f"⚠️  [archive] 文件写入失败 key={key}: {e}")
        file_path = ""
        file_errors = 1

    # 8. 准备写入数据库的聚合条目
    db_records = [{
        "key": key,
        "value": combined_content,
        "keywords": kw_str,
        "file_path": file_path,
        "emotion_tag": "calm",
        "emotional_intensity": 0,
        "importance": 3,
    }]
    archived_ids = [conv["id"] for conv in conversations]

    # 9. 写入数据库并清理 conversations 表
    async with AsyncSessionLocal() as db:
        try:
            inserted = await bulk_save_archived_conversations(db, db_records)
            print(f"✅ [archive] 已写入数据库 {inserted} 条聚合长期记忆")
        except Exception as e:
            print(f"❌ [archive] 数据库写入失败: {e}")
            return {
                "success": False,
                "message": f"数据库写入失败：{str(e)}",
                "error_code": "DB_ERROR"
            }

        try:
            await delete_conversations_by_ids(db, archived_ids)
            print(f"✅ [archive] 已从 conversations 表删除 {len(archived_ids)} 条（FAISS 向量保留）")
        except Exception as e:
            print(f"⚠️  [archive] 删除 conversations 失败: {e}")

    remaining = total - len(archived_ids)
    print(
        f"✅ [archive] 归档完成: 共归档 {len(archived_ids)} 条原始对话, "
        f"聚合保存 1 条长期记忆, 文件错误数 {file_errors}, 剩余对话 {remaining} 条"
    )

    return {
        "success": True,
        "message": f"已归档 {len(archived_ids)} 条对话并生成总结（剩余 {remaining} 条）",
        "data": {
            "archived_count": len(archived_ids),
            "file_errors": file_errors,
            "remaining": remaining,
        }
    }


@router.post("/memory/export")
async def export_memory(user_id: str = "依洛沐"):
    """
    导出用户的所有记忆数据（用于备份或迁移）
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
    """
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / file.filename
    
    try:
        with open(temp_file, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
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
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"⚠️  清理临时文件失败: {e}")


@router.post("/memory")
async def add_memory(req: MemoryRequest):
    """手动保存通用记忆"""
    await save_memory(req.user_id, req.content)
    return {"status": "ok", "msg": "记忆已保存"}


@router.post("/memory/confirm")
async def confirm_memory(req: MemoryConfirmRequest):
    """确认保存触发检测到的记忆"""
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


# ─────────────────────────────────────────────────────────
# 系统配置接口（文字生成、TTS、图升文、画面识别模型及提示词）
# ─────────────────────────────────────────────────────────

class SystemConfigResponse(BaseModel):
    # LLM
    llm_model: str
    llm_api_key: str
    llm_api_base: str
    
    # TTS
    tts_engine: str
    gpt_weights: str
    sovits_weights: str
    ref_audio_path: str
    prompt_text: str
    prompt_lang: str
    text_lang: str
    speed_factor: float
    
    # Image to Text
    image_to_text_model: str
    image_to_text_api_key: str
    image_to_text_api_base: str
    
    # Scene Recognition
    scene_recognition_model: str
    scene_recognition_api_key: str
    scene_recognition_api_base: str
    
    # Embedding (RAG)
    embedding_mode: str
    embedding_api_key: str
    embedding_api_base: str
    embedding_model: str
    embedding_dimension: int
    local_embedding_model: str
    local_embedding_dimension: int
    
    # Multi-provider API Keys & Choices
    provider_deepseek_key: str
    provider_qwen_key: str
    provider_doubao_key: str
    provider_openai_key: str
    provider_custom_base: str
    provider_custom_key: str
    
    llm_provider: str
    image_to_text_provider: str
    scene_recognition_provider: str
    embedding_provider: str
    
    # Prompt
    system_prompt: str
    
    # Agent info (Read-only)
    agent_info: Optional[Dict[str, Any]] = None


class SystemConfigRequest(BaseModel):
    # LLM
    llm_model: str
    llm_api_key: str
    llm_api_base: str
    
    # TTS
    tts_engine: str
    gpt_weights: str
    sovits_weights: str
    ref_audio_path: str
    prompt_text: str
    prompt_lang: str
    text_lang: str
    speed_factor: float
    
    # Image to Text
    image_to_text_model: str
    image_to_text_api_key: str
    image_to_text_api_base: str
    
    # Scene Recognition
    scene_recognition_model: str
    scene_recognition_api_key: str
    scene_recognition_api_base: str
    
    # Embedding (RAG)
    embedding_mode: str
    embedding_api_key: str
    embedding_api_base: str
    embedding_model: str
    embedding_dimension: int
    local_embedding_model: str
    local_embedding_dimension: int
    
    # Multi-provider API Keys & Choices
    provider_deepseek_key: str
    provider_qwen_key: str
    provider_doubao_key: str
    provider_openai_key: str
    provider_custom_base: str
    provider_custom_key: str
    
    llm_provider: str
    image_to_text_provider: str
    scene_recognition_provider: str
    embedding_provider: str
    
    # Prompt
    system_prompt: str
    
    # Agent info (Read-only, optional for incoming requests)
    agent_info: Optional[Dict[str, Any]] = None


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """获取系统的当前配置与 Prompt 提示词"""
    import config
    from core.person import get_base_person, BASE_PERSON
    
    return {
        # LLM
        "llm_model": config.LLM_MODEL,
        "llm_api_key": config.LLM_API_KEY,
        "llm_api_base": config.LLM_API_BASE,
        
        # TTS
        "tts_engine": config.TTS_ENGINE,
        "gpt_weights": config.GPT_SOVITS_GPT_WEIGHTS,
        "sovits_weights": config.GPT_SOVITS_SOVITS_WEIGHTS,
        "ref_audio_path": config.GPT_SOVITS_REF_AUDIO_PATH,
        "prompt_text": config.GPT_SOVITS_PROMPT_TEXT,
        "prompt_lang": config.GPT_SOVITS_PROMPT_LANG,
        "text_lang": config.GPT_SOVITS_TEXT_LANG,
        "speed_factor": config.GPT_SOVITS_SPEED_FACTOR,
        
        # Image
        "image_to_text_model": config.IMAGE_TO_TEXT_MODEL,
        "image_to_text_api_key": config.IMAGE_TO_TEXT_API_KEY,
        "image_to_text_api_base": config.IMAGE_TO_TEXT_API_BASE,
        
        # Scene
        "scene_recognition_model": config.SCENE_RECOGNITION_MODEL,
        "scene_recognition_api_key": config.SCENE_RECOGNITION_API_KEY,
        "scene_recognition_api_base": config.SCENE_RECOGNITION_API_BASE,
        
        # Embedding
        "embedding_mode": config.EMBEDDING_MODE,
        "embedding_api_key": config.EMBEDDING_API_KEY,
        "embedding_api_base": config.EMBEDDING_API_BASE,
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dimension": config.EMBEDDING_DIMENSION,
        "local_embedding_model": config.LOCAL_EMBEDDING_MODEL,
        "local_embedding_dimension": config.LOCAL_EMBEDDING_DIMENSION,
        
        # Multi-provider API Keys & Choices
        "provider_deepseek_key": config.PROVIDER_DEEPSEEK_KEY,
        "provider_qwen_key": config.PROVIDER_QWEN_KEY,
        "provider_doubao_key": config.PROVIDER_DOUBAO_KEY,
        "provider_openai_key": config.PROVIDER_OPENAI_KEY,
        "provider_custom_base": config.PROVIDER_CUSTOM_BASE,
        "provider_custom_key": config.PROVIDER_CUSTOM_KEY,
        
        "llm_provider": config.LLM_PROVIDER,
        "image_to_text_provider": config.IMAGE_TO_TEXT_PROVIDER,
        "scene_recognition_provider": config.SCENE_RECOGNITION_PROVIDER,
        "embedding_provider": config.EMBEDDING_PROVIDER,
        
        # Prompt
        "system_prompt": get_base_person(),
        
        # Agent Info (Read-only)
        "agent_info": {
            "name": "八重樱 (Yae Sakura)",
            "identity": "原八重村巫女，现为圣痕空间中的永恒守护者（真炎幸魂姿态）。",
            "personality": ["沉静", "克制", "内敛", "温柔深沉", "坚韧执着"],
            "hobbies": ["练习剑术", "制作料理 (如樱花豆腐)", "在樱花树下散步", "守护重要之人"],
            "mood": "平静 (Calm) - 正在圣痕空间中静静守护",
            "base_prompt": BASE_PERSON,
            "consts": {
                "core_contradiction": "一个为悲剧命运所困、温柔而执着的灵魂，在无尽的牺牲与守望中，寻找属于自己的微小救赎与安宁。",
                "abilities": "擅长剑术、厨艺，通晓祭祀与医疗之道。因长期守护圣痕空间，对现代文明已有所了解，但内心更眷恋旧日八重村的事物。",
                "forbidden": "不使用 emoji、表情符号、Markdown 格式、列表符号。不说\"作为 AI\"、\"我是语言模型\"、\"我没有情感\"等。"
            }
        }
    }


@router.put("/config")
async def update_system_config(req: SystemConfigRequest):
    """修改并动态生效系统的配置与 Prompt 提示词"""
    import config
    from core.person import PROMPT_FILE
    
    # 1. 保存 Prompt 提示词到文件
    try:
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(req.system_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存系统提示词失败: {e}")
        
    # 2. 根据选定的 provider 动态计算出底层的 API BASE & API KEY
    PROVIDER_BASES = {
        "deepseek": "https://api.deepseek.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "doubao": "https://ark.cn-beijing.volces.com/api/v3",
        "openai": "https://api.openai.com/v1",
        "custom": ""
    }
    
    def resolve_provider_base_key(provider):
        if provider == "custom":
            return req.provider_custom_base, req.provider_custom_key
        
        base_url = PROVIDER_BASES.get(provider, "")
        key_map = {
            "deepseek": req.provider_deepseek_key,
            "qwen": req.provider_qwen_key,
            "doubao": req.provider_doubao_key,
            "openai": req.provider_openai_key
        }
        return base_url, key_map.get(provider, "")
        
    llm_base, llm_key = resolve_provider_base_key(req.llm_provider)
    img_base, img_key = resolve_provider_base_key(req.image_to_text_provider)
    scene_base, scene_key = resolve_provider_base_key(req.scene_recognition_provider)
    embed_base, embed_key = resolve_provider_base_key(req.embedding_provider)
    
    # 3. 保存并更新其他配置项到 settings.json 并热生效
    new_settings = {
        "LLM_MODEL": req.llm_model,
        "LLM_API_KEY": llm_key,
        "LLM_API_BASE": llm_base,
        
        "TTS_ENGINE": req.tts_engine,
        "GPT_SOVITS_GPT_WEIGHTS": req.gpt_weights,
        "GPT_SOVITS_SOVITS_WEIGHTS": req.sovits_weights,
        "GPT_SOVITS_REF_AUDIO_PATH": req.ref_audio_path,
        "GPT_SOVITS_PROMPT_TEXT": req.prompt_text,
        "GPT_SOVITS_PROMPT_LANG": req.prompt_lang,
        "GPT_SOVITS_TEXT_LANG": req.text_lang,
        "GPT_SOVITS_SPEED_FACTOR": req.speed_factor,
        
        "IMAGE_TO_TEXT_MODEL": req.image_to_text_model,
        "IMAGE_TO_TEXT_API_KEY": img_key,
        "IMAGE_TO_TEXT_API_BASE": img_base,
        
        "SCENE_RECOGNITION_MODEL": req.scene_recognition_model,
        "SCENE_RECOGNITION_API_KEY": scene_key,
        "SCENE_RECOGNITION_API_BASE": scene_base,
        
        "EMBEDDING_MODE": req.embedding_mode,
        "EMBEDDING_API_KEY": embed_key,
        "EMBEDDING_API_BASE": embed_base,
        "EMBEDDING_MODEL": req.embedding_model,
        "EMBEDDING_DIMENSION": req.embedding_dimension,
        "LOCAL_EMBEDDING_MODEL": req.local_embedding_model,
        "LOCAL_EMBEDDING_DIMENSION": req.local_embedding_dimension,
        
        # 保存厂商具体数据和选择
        "PROVIDER_DEEPSEEK_KEY": req.provider_deepseek_key,
        "PROVIDER_QWEN_KEY": req.provider_qwen_key,
        "PROVIDER_DOUBAO_KEY": req.provider_doubao_key,
        "PROVIDER_OPENAI_KEY": req.provider_openai_key,
        "PROVIDER_CUSTOM_BASE": req.provider_custom_base,
        "PROVIDER_CUSTOM_KEY": req.provider_custom_key,
        
        "LLM_PROVIDER": req.llm_provider,
        "IMAGE_TO_TEXT_PROVIDER": req.image_to_text_provider,
        "SCENE_RECOGNITION_PROVIDER": req.scene_recognition_provider,
        "EMBEDDING_PROVIDER": req.embedding_provider,
    }
    
    success = config.save_dynamic_settings(new_settings)
    if success:
        return {"status": "ok", "msg": "系统配置及提示词已保存，并已即时生效！"}
    else:
        raise HTTPException(status_code=500, detail="保存系统配置文件 settings.json 失败")

