"""
keyword_extractor.py
调用 LLM 从记忆内容中提取 5~10 个检索关键词。
提取失败时静默降级，返回空列表，不阻断主流程。

新增批量接口 extract_keywords_batch()：
  - 将多条内容分批打包到单次 LLM 请求（每批最多 BATCH_SIZE 条）
  - 归档 150 条时约需 5 次 LLM 调用，而非 150 次
"""

import re
from typing import List
from llm.adapter import generate


# 单条提取 prompt
_KEYWORD_PROMPT = """你是一个信息提取助手。
请从以下记忆内容中，提取5到10个最能帮助日后检索此条记忆的关键词。
要求：
- 关键词应为名词或短语，聚焦实体、概念、事件、人名等核心信息
- 用中文顿号「、」分隔
- 只输出关键词列表，不要任何其他文字

记忆内容：{content}"""


# 批量提取 prompt
_BATCH_KEYWORD_PROMPT = """你是一个信息提取助手。
请为以下每条对话记录分别提取5到10个最能帮助日后检索的关键词。

要求：
- 关键词应为名词或短语，聚焦实体、概念、事件、人名等核心信息
- 严格按格式输出，每行一条，用序号对应，关键词之间用顿号「、」分隔
- 只输出关键词行，不要任何其他文字

对话列表：
{items}

输出格式示例（严格遵守，序号冒号后紧跟关键词）：
1: 关键词A、关键词B、关键词C
2: 关键词D、关键词E
3: 关键词F、关键词G、关键词H"""


# 每批最多处理的条数
BATCH_SIZE = 30


async def extract_keywords(content: str) -> List[str]:
    """
    从单条记忆内容中提取 5~10 个关键词。

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


async def extract_keywords_batch(contents: List[str]) -> List[List[str]]:
    """
    批量提取关键词，每批最多 BATCH_SIZE 条，合并为一次 LLM 请求。

    归档 150 条时约调用 ceil(150/30)=5 次 LLM，而非 150 次。
    任意一批失败时该批降级返回空列表，不影响其他批次。

    Args:
        contents: 多条记忆文本列表

    Returns:
        与 contents 等长的关键词列表的列表，每个元素为对应内容的关键词列表。
        提取失败的条目返回空列表 []。
    """
    if not contents:
        return []

    all_keywords: List[List[str]] = []

    for i in range(0, len(contents), BATCH_SIZE):
        batch = contents[i:i + BATCH_SIZE]
        batch_result = await _extract_one_batch(batch, start_index=i)
        all_keywords.extend(batch_result)

    return all_keywords


async def _extract_one_batch(contents: List[str], start_index: int = 0) -> List[List[str]]:
    """
    对单个批次调用 LLM，解析批量输出。

    Args:
        contents: 本批次的内容列表
        start_index: 批次在全局列表中的起始下标（仅用于日志）

    Returns:
        与 contents 等长的关键词列表
    """
    items_str = "\n".join(
        f"{i + 1}. {c.strip()}" for i, c in enumerate(contents)
    )
    prompt = _BATCH_KEYWORD_PROMPT.format(items=items_str)

    try:
        raw = await generate(prompt)
        result = _parse_batch_output(raw, len(contents))
        print(
            f"✅ [keyword_extractor] 批量提取完成: 第{start_index + 1}~{start_index + len(contents)}条"
        )
        return result
    except Exception as e:
        print(
            f"⚠️ [keyword_extractor] 批量提取失败（第{start_index + 1}~{start_index + len(contents)}条），"
            f"已降级为空列表: {e}"
        )
        return [[] for _ in contents]


def _parse_batch_output(raw: str, count: int) -> List[List[str]]:
    """
    解析批量 LLM 输出。

    期望格式：
        1: 关键词A、关键词B
        2: 关键词C、关键词D

    无法解析的行对应位置降级为空列表。
    """
    results: List[List[str]] = [[] for _ in range(count)]

    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # 匹配 "数字: 关键词" 或 "数字. 关键词"
        m = re.match(r'^(\d+)[.：:]\s*(.+)$', line)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < count:
                results[idx] = _parse_keywords(m.group(2))

    return results


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
