"""
compression.py
对话压缩服务 - 使用LLM将短期对话总结为长期记忆

职责：
1. 调用LLM API压缩对话列表
2. 实现重试机制和超时处理
3. 提供降级策略（简单文本拼接）
"""

import asyncio
from typing import List, Dict
from datetime import datetime

from llm.adapter import generate
from config import LLM_API_KEY, LLM_API_BASE, LLM_MODEL


class CompressionError(Exception):
    """压缩服务异常"""
    pass


def build_compression_prompt(conversations: List[Dict], user_id: str, role: str = "default") -> str:
    """
    构建压缩提示词
    
    Args:
        conversations: 对话列表
        user_id: 用户ID
        role: 角色类型
        
    Returns:
        压缩提示词
    """
    # 格式化对话历史
    conversation_text = "\n".join([
        f"[{conv['timestamp']}] {conv['role']}: {conv['content']}"
        for conv in conversations
    ])
    
    prompt = f"""请将以下对话历史压缩总结为结构化的长期记忆。

对话历史（共{len(conversations)}条）：
{conversation_text}

请按以下格式输出总结：

## 重要事件
- 列出对话中提到的重要事件和时间点

## 情感变化
- 描述对话中的情绪变化和情感要点

## 关键信息
- 提取对话中的关键信息（人物、地点、偏好等）

## 对话主题
- 总结对话的主要话题和讨论内容

要求：
1. 保留重要细节，去除冗余信息
2. 使用简洁的语言，避免重复
3. 按重要性排序
4. 总结长度控制在500字以内
"""
    
    return prompt


async def call_llm_with_retry(prompt: str, max_retries: int = 3) -> str:
    """
    带重试的LLM调用
    
    Args:
        prompt: 提示词
        max_retries: 最大重试次数
        
    Returns:
        LLM生成的文本
        
    Raises:
        CompressionError: LLM调用失败
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = await generate(prompt)
            if not response or len(response.strip()) == 0:
                raise CompressionError("LLM返回空响应")
            return response
        except asyncio.TimeoutError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                print(f"⚠️  [compression] LLM调用超时，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ [compression] LLM调用超时，已达最大重试次数")
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  [compression] LLM调用失败: {e}，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ [compression] LLM调用失败: {e}")
    
    raise CompressionError(f"LLM调用失败（已重试{max_retries}次）: {str(last_error)}")


def fallback_compression(conversations: List[Dict]) -> str:
    """
    降级压缩策略：简单文本拼接
    
    当LLM服务不可用时使用此方法
    
    Args:
        conversations: 对话列表
        
    Returns:
        简单拼接的文本
    """
    # 只保留最后20条对话
    recent_conversations = conversations[-20:] if len(conversations) > 20 else conversations
    
    summary_lines = [
        f"# 对话归档 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        f"",
        f"共 {len(conversations)} 条对话，以下是最近的 {len(recent_conversations)} 条：",
        f""
    ]
    
    for conv in recent_conversations:
        timestamp = conv.get('timestamp', '')
        role = conv.get('role', 'unknown')
        content = conv.get('content', '')[:200]  # 限制长度
        summary_lines.append(f"- [{timestamp}] {role}: {content}")
    
    return "\n".join(summary_lines)


async def compress_conversations(
    conversations: List[Dict],
    user_id: str,
    role: str = "default"
) -> str:
    """
    压缩对话列表为总结文本
    
    Args:
        conversations: 对话列表，每个对话包含 role, content, timestamp 等字段
        user_id: 用户ID
        role: 角色类型
        
    Returns:
        压缩后的总结文本
        
    Raises:
        CompressionError: 压缩失败（仅在降级策略也失败时抛出）
    """
    if not conversations:
        raise CompressionError("对话列表为空，无法压缩")
    
    try:
        # 尝试使用LLM压缩
        print(f"🔄 [compression] 开始压缩 {len(conversations)} 条对话...")
        prompt = build_compression_prompt(conversations, user_id, role)
        summary = await call_llm_with_retry(prompt)
        print(f"✅ [compression] LLM压缩成功，生成 {len(summary)} 字符")
        return summary
        
    except Exception as e:
        # LLM失败，使用降级策略
        print(f"⚠️  [compression] LLM压缩失败，使用降级方案: {e}")
        try:
            summary = fallback_compression(conversations)
            print(f"✅ [compression] 降级压缩成功，生成 {len(summary)} 字符")
            return summary
        except Exception as fallback_error:
            # 降级策略也失败
            print(f"❌ [compression] 降级压缩也失败: {fallback_error}")
            raise CompressionError(f"压缩失败: {str(e)}, 降级失败: {str(fallback_error)}")


async def compress_conversations_batch(
    conversations_list: List[List[Dict]],
    user_id: str,
    role: str = "default"
) -> List[str]:
    """
    批量压缩多个对话列表
    
    Args:
        conversations_list: 对话列表的列表
        user_id: 用户ID
        role: 角色类型
        
    Returns:
        压缩后的总结文本列表
    """
    tasks = [
        compress_conversations(conversations, user_id, role)
        for conversations in conversations_list
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
