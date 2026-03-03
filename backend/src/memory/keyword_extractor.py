"""
keyword_extractor.py
调用 LLM 从记忆内容中提取 5~10 个检索关键词。
提取失败时静默降级，返回空列表，不阻断主流程。
"""

import re
from typing import List
from llm.adapter import generate


_KEYWORD_PROMPT = """你是一个信息提取助手。
请从以下记忆内容中，提取5到10个最能帮助日后检索此条记忆的关键词。
要求：
- 关键词应为名词或短语，聚焦实体、概念、事件、人名等核心信息
- 用中文顿号「、」分隔
- 只输出关键词列表，不要任何其他文字

记忆内容：{content}"""


async def extract_keywords(content: str) -> List[str]:
    """
    从记忆内容中提取 5~10 个关键词。
    
    Args:
        content: 记忆的文本内容
        
    Returns:
        关键词列表，最多10个。提取失败时返回空列表。
    """
    if not content or not content.strip():
        return []

    prompt = _KEYWORD_PROMPT.format(content=content.strip())

    try:
        raw = await generate(prompt)
        return _parse_keywords(raw)
    except Exception as e:
        print(f"⚠️ [keyword_extractor] 关键词提取失败，已降级为空列表: {e}")
        return []


def _parse_keywords(raw: str) -> List[str]:
    """
    解析 LLM 输出的关键词字符串。
    支持顿号、逗号、空格等多种分隔符，最多保留 10 个词。
    
    Args:
        raw: LLM 返回的原始字符串
        
    Returns:
        清洗后的关键词列表
    """
    if not raw:
        return []

    # 统一替换多种分隔符为逗号
    normalized = re.sub(r'[、，,\s]+', ',', raw.strip())

    keywords = [kw.strip() for kw in normalized.split(',') if kw.strip()]

    # 过滤掉过长的"词"（LLM 有时会夹带整句话）
    keywords = [kw for kw in keywords if len(kw) <= 20]

    # 最多保留 10 个
    return keywords[:10]


def keywords_to_str(keywords: List[str]) -> str:
    """将关键词列表转为逗号分隔字符串，用于写入数据库。"""
    return ",".join(keywords)


def str_to_keywords(keywords_str: str) -> List[str]:
    """将数据库中的关键词字符串还原为列表。"""
    if not keywords_str:
        return []
    return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
