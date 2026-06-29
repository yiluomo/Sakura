"""
vector_store.py
向量存储管理模块（FAISS实现）

职责：
1. 初始化 FAISS 索引
2. 生成文本的向量表示（embedding）
3. 向量的增删改查
4. 语义相似度检索
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import faiss
from openai import AsyncOpenAI

from config import (
    VECTOR_STORE_DIR,
    EMBEDDING_MODE,
    LOCAL_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_DIMENSION,
    EMBEDDING_API_KEY,
    EMBEDDING_API_BASE,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    ACTUAL_EMBEDDING_DIMENSION,
    VECTOR_SEARCH_LIMIT,
    VECTOR_SEARCH_SCORE_THRESHOLD,
)


# ─────────────────────────────────────────────
# 全局变量
# ─────────────────────────────────────────────

# FAISS 索引文件路径
INDEX_FILE = VECTOR_STORE_DIR / "conversations.index"
METADATA_FILE = VECTOR_STORE_DIR / "metadata.json"
ID_MAPPING_FILE = VECTOR_STORE_DIR / "id_mapping.json"

# 全局索引和元数据
_faiss_index = None
_metadata = {}  # {vector_id: {conversation_id, user_id, role, content, ...}}
_id_mapping = {}  # {vector_id: faiss_internal_id}
_reverse_mapping = {}  # {faiss_internal_id: vector_id}

# 本地 Embedding 模型
_local_model = None

# OpenAI 客户端（用于生成 embedding）
openai_client = AsyncOpenAI(
    api_key=EMBEDDING_API_KEY or "placeholder",
    base_url=EMBEDDING_API_BASE or "https://api.openai.com/v1",
)

# 异步后台任务所需参数
import asyncio
from concurrent.futures import ThreadPoolExecutor

_is_dirty = False
_save_executor = ThreadPoolExecutor(max_workers=1)


# ─────────────────────────────────────────────
# 初始化
# ─────────────────────────────────────────────

def _load_local_model():
    """加载本地 Embedding 模型"""
    global _local_model
    
    if EMBEDDING_MODE != "local":
        return
    
    if _local_model is not None:
        return
    
    try:
        # 设置 HuggingFace 镜像加速下载
        import os
        if 'HF_ENDPOINT' not in os.environ:
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        
        from sentence_transformers import SentenceTransformer
        print(f"🔄 加载本地 Embedding 模型: {LOCAL_EMBEDDING_MODEL}")
        print(f"   (首次运行会自动下载模型，请耐心等待...)")
        _local_model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
        print(f"✅ 本地模型加载完成")
    except Exception as e:
        print(f"❌ 加载本地模型失败: {e}")
        print(f"   请运行: pip install sentence-transformers")
        raise


def _load_index():
    """加载 FAISS 索引和元数据"""
    global _faiss_index, _metadata, _id_mapping, _reverse_mapping
    
    if INDEX_FILE.exists():
        _faiss_index = faiss.read_index(str(INDEX_FILE))
        print(f"✅ 加载 FAISS 索引: {_faiss_index.ntotal} 条向量")
    else:
        _faiss_index = faiss.IndexFlatIP(ACTUAL_EMBEDDING_DIMENSION)  # 内积（余弦相似度）
        print(f"✅ 创建新的 FAISS 索引 (维度: {ACTUAL_EMBEDDING_DIMENSION})")
    
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            _metadata = json.load(f)
    
    if ID_MAPPING_FILE.exists():
        with open(ID_MAPPING_FILE, 'r', encoding='utf-8') as f:
            _id_mapping = json.load(f)
            _reverse_mapping = {v: k for k, v in _id_mapping.items()}


def _save_index():
    """保存 FAISS 索引和元数据"""
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    faiss.write_index(_faiss_index, str(INDEX_FILE))
    
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(_metadata, f, ensure_ascii=False, indent=2)
    
    with open(ID_MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(_id_mapping, f, ensure_ascii=False, indent=2)


def init_collection():
    """
    初始化向量存储（应用启动时调用一次）
    """
    try:
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        
        # 加载本地模型（如果使用本地模式）
        if EMBEDDING_MODE == "local":
            _load_local_model()
        
        _load_index()
        
        mode_info = f"本地模型 ({LOCAL_EMBEDDING_MODEL})" if EMBEDDING_MODE == "local" else f"API ({EMBEDDING_MODEL})"
        print(f"✅ 向量存储初始化完成 - 模式: {mode_info}")
        return True
    except Exception as e:
        print(f"❌ 初始化向量存储失败: {e}")
        return False


async def start_periodic_save():
    """后台定时任务：每 5 分钟检查一次是否需要保存到磁盘"""
    global _is_dirty
    while True:
        await asyncio.sleep(300)  # 5 分钟
        if _is_dirty:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(_save_executor, _save_index)
            _is_dirty = False


def force_save_index():
    """手动同步保存（主要用于服务关闭时调用）"""
    global _is_dirty
    if _is_dirty:
        _save_index()
        _is_dirty = False


# ─────────────────────────────────────────────
# Embedding 生成
# ─────────────────────────────────────────────

async def generate_embedding(text: str) -> List[float]:
    """
    生成文本的向量表示
    
    Args:
        text: 输入文本
        
    Returns:
        向量列表（长度为 ACTUAL_EMBEDDING_DIMENSION）
    """
    try:
        if EMBEDDING_MODE == "local":
            # 使用本地模型
            if _local_model is None:
                _load_local_model()
            
            # 生成向量
            embedding = _local_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        else:
            # 使用 API
            response = await openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
            )
            embedding = response.data[0].embedding
            # 归一化（用于余弦相似度）
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = (np.array(embedding) / norm).tolist()
            return embedding
    except Exception as e:
        print(f"❌ 生成 embedding 失败: {e}")
        return [0.0] * ACTUAL_EMBEDDING_DIMENSION


# ─────────────────────────────────────────────
# 向量操作
# ─────────────────────────────────────────────

def generate_vector_id(user_id: str, conversation_id: int) -> str:
    """生成向量 ID（确保唯一性）"""
    return f"{user_id}_{conversation_id}"


async def add_conversation_vector(
    user_id: str,
    conversation_id: int,
    role: str,
    content: str,
    emotion_type: str = "calm",
    importance: int = 3,
    timestamp: datetime = None,
) -> str:
    """
    为对话生成向量并存入 FAISS
    
    Args:
        user_id: 用户 ID
        conversation_id: 对话 ID（MySQL 主键）
        role: 角色（user/sakura）
        content: 对话内容
        emotion_type: 情绪类型
        importance: 重要度
        timestamp: 时间戳
        
    Returns:
        vector_id: 向量 ID
    """
    try:
        global _is_dirty
        
        # 1. 生成向量
        vector = await generate_embedding(content)
        vector_np = np.array([vector], dtype=np.float32)
        
        # 2. 生成向量 ID
        vector_id = generate_vector_id(user_id, conversation_id)
        
        # 3. 添加到 FAISS 索引
        faiss_id = _faiss_index.ntotal
        _faiss_index.add(vector_np)
        
        # 4. 保存映射和元数据
        _id_mapping[vector_id] = faiss_id
        _reverse_mapping[faiss_id] = vector_id
        
        _metadata[vector_id] = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "emotion_type": emotion_type,
            "importance": importance,
            "timestamp": (timestamp or datetime.now()).isoformat(),
        }
        
        # 5. 标记脏数据，等待异步定时写入
        _is_dirty = True
        
        return vector_id
        
    except Exception as e:
        print(f"❌ 添加向量失败 conversation_id={conversation_id}: {e}")
        return ""


async def search_similar_conversations(
    user_id: str,
    query_text: str,
    limit: int = VECTOR_SEARCH_LIMIT,
    score_threshold: float = VECTOR_SEARCH_SCORE_THRESHOLD,
    time_filter: Optional[Dict] = None,
) -> List[Dict]:
    """
    语义相似度检索
    
    Args:
        user_id: 用户 ID
        query_text: 查询文本
        limit: 返回数量
        score_threshold: 相似度阈值（0-1）
        time_filter: 时间过滤条件（暂不支持）
        
    Returns:
        相似对话列表
    """
    try:
        if _faiss_index.ntotal == 0:
            return []
        
        # 1. 生成查询向量
        query_vector = await generate_embedding(query_text)
        query_np = np.array([query_vector], dtype=np.float32)
        
        # 2. 搜索（搜索更多结果用于过滤）
        k = min(_faiss_index.ntotal, limit * 3)
        distances, indices = _faiss_index.search(query_np, k)
        
        # 3. 过滤并格式化结果
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            
            vector_id = _reverse_mapping.get(idx)
            if not vector_id:
                continue
            
            meta = _metadata.get(vector_id)
            if not meta:
                continue
            
            # 过滤用户
            if meta["user_id"] != user_id:
                continue
            
            # 相似度阈值
            score = float(dist)
            if score < score_threshold:
                continue
            
            results.append({
                "conversation_id": meta["conversation_id"],
                "content": meta["content"],
                "role": meta["role"],
                "emotion_type": meta.get("emotion_type", "calm"),
                "importance": meta.get("importance", 3),
                "timestamp": meta["timestamp"],
                "score": score,
            })
            
            if len(results) >= limit:
                break
        
        return results
        
    except Exception as e:
        print(f"❌ 向量检索失败: {e}")
        return []


def delete_conversation_vector(user_id: str, conversation_id: int) -> bool:
    """
    删除对话向量（FAISS不支持删除，标记为已删除）
    
    Args:
        user_id: 用户 ID
        conversation_id: 对话 ID
        
    Returns:
        是否成功
    """
    try:
        global _is_dirty
        vector_id = generate_vector_id(user_id, conversation_id)
        
        # 从元数据中删除
        if vector_id in _metadata:
            del _metadata[vector_id]
        
        if vector_id in _id_mapping:
            faiss_id = _id_mapping[vector_id]
            del _id_mapping[vector_id]
            if faiss_id in _reverse_mapping:
                del _reverse_mapping[faiss_id]
        
        _is_dirty = True
        return True
    except Exception as e:
        print(f"❌ 删除向量失败 conversation_id={conversation_id}: {e}")
        return False


def get_collection_stats() -> Dict:
    """
    获取集合统计信息
    
    Returns:
        统计信息字典
    """
    try:
        return {
            "vectors_count": _faiss_index.ntotal if _faiss_index else 0,
            "metadata_count": len(_metadata),
            "storage_path": str(VECTOR_STORE_DIR),
        }
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        return {}
