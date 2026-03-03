"""
file_store.py
长期记忆文件存储模块。
负责将记忆内容以 Markdown 格式写入 memory_store/ 目录下的对应文件。
数据库作为轻量索引，文件存储完整可读内容。
"""

import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import aiofiles

from config import MEMORY_STORE_DIR


# ─────────────────────────────────────────────
# 全局写锁（单用户，串行化所有写操作）
# ─────────────────────────────────────────────
_write_lock = asyncio.Lock()


# ─────────────────────────────────────────────
# memory_type → 文件名 映射
# ─────────────────────────────────────────────
_TYPE_TO_FILE = {
    "name":                 "profile.md",
    "age":                  "profile.md",
    "birthday":             "profile.md",
    "location":             "profile.md",
    "occupation":           "profile.md",
    "family":               "profile.md",
    "friend":               "profile.md",
    "hobby":                "preferences.md",
    "dislike":              "preferences.md",
    "experience":           "preferences.md",
    "manual":               "notes.md",
    "conversation_summary": "summaries.md",
}

# 文件标题
_FILE_TITLES = {
    "profile.md":     "# 个人档案",
    "preferences.md": "# 偏好与经历",
    "notes.md":       "# 手动笔记",
    "summaries.md":   "# 对话摘要记录",
}

# memory_type → 可读中文标题
_TYPE_TO_TITLE = {
    "name":                 "姓名",
    "age":                  "年龄",
    "birthday":             "生日",
    "location":             "居住地",
    "occupation":           "职业",
    "family":               "家人",
    "friend":               "朋友",
    "hobby":                "爱好",
    "dislike":              "厌恶",
    "experience":           "经历",
    "manual":               "备忘",
    "conversation_summary": "对话摘要",
}


# ─────────────────────────────────────────────
# 路径工具
# ─────────────────────────────────────────────

def get_target_file(memory_type: str) -> Path:
    """根据 memory_type 返回对应 .md 文件的绝对路径。"""
    filename = _TYPE_TO_FILE.get(memory_type, "notes.md")
    return MEMORY_STORE_DIR / filename


def get_relative_path(memory_type: str) -> str:
    """返回相对路径字符串，用于写入数据库 file_path 字段。"""
    filename = _TYPE_TO_FILE.get(memory_type, "notes.md")
    return f"memory_store/{filename}"


# ─────────────────────────────────────────────
# 文件读写
# ─────────────────────────────────────────────

async def _read_file(filepath: Path) -> str:
    """异步读取文件，文件不存在时返回空字符串。"""
    if not filepath.exists():
        return ""
    async with aiofiles.open(filepath, encoding="utf-8") as f:
        return await f.read()


async def _write_file(filepath: Path, content: str) -> None:
    """异步写入文件（覆盖）。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as f:
        await f.write(content)


def _build_entry_block(memory_type: str, key: str, content: str,
                       keywords: List[str], importance: int) -> str:
    """
    构建一个 Markdown 记忆条目块。
    以 <!-- entry: type/key --> 注释作为程序定位标识。
    """
    title = _TYPE_TO_TITLE.get(memory_type, memory_type)
    kw_str = " ".join([f"`{kw}`" for kw in keywords]) if keywords else "（无）"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"\n<!-- entry: {memory_type}/{key} -->\n"
        f"## {title}\n"
        f"**内容**：{content}  \n"
        f"**关键词**：{kw_str}  \n"
        f"**重要度**：{importance}  \n"
        f"**更新时间**：{now}\n\n"
        f"---\n"
    )


def _build_summary_entry_block(key: str, content: str,
                                keywords: List[str]) -> str:
    """
    构建对话摘要专用条目块（summaries.md 格式，内容较长）。
    """
    kw_str = " ".join([f"`{kw}`" for kw in keywords]) if keywords else "（无）"
    # key 格式：2026-03-01_to_2026-03-03
    title = key.replace("_to_", " 至 ").replace("_", "-")

    return (
        f"\n<!-- entry: conversation_summary/{key} -->\n"
        f"## {title}\n"
        f"**关键词**：{kw_str}  \n"
        f"**摘要**：  \n"
        f"{content}\n\n"
        f"---\n"
    )


# ─────────────────────────────────────────────
# 核心写入函数
# ─────────────────────────────────────────────

async def write_entry(memory_type: str, key: str, content: str,
                      keywords: List[str], importance: int = 3) -> None:
    """
    写入或更新单条记忆到对应的 .md 文件。
    - 找到已有 <!-- entry: type/key --> 注释 → 替换整个条目块
    - 未找到 → 追加到文件末尾
    
    使用全局写锁保障并发安全。
    """
    filepath = get_target_file(memory_type)

    # 构建新的条目文本
    if memory_type == "conversation_summary":
        new_block = _build_summary_entry_block(key, content, keywords)
    else:
        new_block = _build_entry_block(memory_type, key, content, keywords, importance)

    async with _write_lock:
        existing = await _read_file(filepath)

        # 文件为空时，添加文件标题头
        if not existing.strip():
            filename = _TYPE_TO_FILE.get(memory_type, "notes.md")
            header = _FILE_TITLES.get(filename, "# 记忆")
            existing = f"{header}\n"

        # 用正则定位"<!-- entry: type/key -->到下一个---"之间的内容
        pattern = re.compile(
            r'\n<!-- entry: ' + re.escape(f"{memory_type}/{key}") + r' -->.*?(?=\n<!-- entry:|\Z)',
            re.DOTALL
        )

        if pattern.search(existing):
            # 找到已有条目 → 替换
            updated = pattern.sub(new_block, existing)
        else:
            # 未找到 → 追加
            updated = existing.rstrip() + "\n" + new_block

        await _write_file(filepath, updated)


# ─────────────────────────────────────────────
# 读取用于 prompt 注入
# ─────────────────────────────────────────────

def _parse_entries_from_file(text: str) -> List[dict]:
    """
    从文件文本中解析所有条目，提取 memory_type、key、content、keywords、importance。
    """
    entries = []
    # 匹配每个条目块
    pattern = re.compile(
        r'<!-- entry: (\w+)/(.+?) -->\n'   # type / key
        r'## .+?\n'                          # 标题行
        r'(.*?)'                             # 条目内容（非贪婪）
        r'(?=\n<!-- entry:|\Z)',             # 到下一个条目或文件末尾
        re.DOTALL
    )
    for m in pattern.finditer(text):
        memory_type = m.group(1)
        key = m.group(2).strip()
        body = m.group(3)

        # 提取 **内容** 或 **摘要**
        content_match = re.search(r'\*\*(?:内容|摘要)\*\*[：:]\s*(.+?)  \n', body)
        content = content_match.group(1).strip() if content_match else ""

        # 提取 **关键词**
        kw_match = re.search(r'\*\*关键词\*\*[：:]\s*(.+?)  \n', body)
        kw_raw = kw_match.group(1).strip() if kw_match else ""
        keywords = [k.strip('`') for k in kw_raw.split() if k.strip('`')]

        # 提取 **重要度**
        imp_match = re.search(r'\*\*重要度\*\*[：:]\s*(\d+)', body)
        importance = int(imp_match.group(1)) if imp_match else 1

        entries.append({
            "memory_type": memory_type,
            "key": key,
            "content": content,
            "keywords": keywords,
            "importance": importance,
        })

    return entries


async def get_top_memories(n: int = 5) -> str:
    """
    读取所有 .md 文件，解析条目，按重要度降序取前 n 条。
    返回格式化的字符串，用于注入对话 prompt。
    
    Args:
        n: 返回条目数量
        
    Returns:
        格式化的记忆文本，若无记忆则返回空字符串
    """
    all_entries = []

    for filename in ["profile.md", "preferences.md", "notes.md", "summaries.md"]:
        filepath = MEMORY_STORE_DIR / filename
        text = await _read_file(filepath)
        if text:
            all_entries.extend(_parse_entries_from_file(text))

    if not all_entries:
        return ""

    # 按重要度降序排列，取前 n 条
    top = sorted(all_entries, key=lambda e: e["importance"], reverse=True)[:n]

    lines = ["【用户长期记忆】"]
    for entry in top:
        title = _TYPE_TO_TITLE.get(entry["memory_type"], entry["memory_type"])
        kw_str = "、".join(entry["keywords"]) if entry["keywords"] else "无"
        content_preview = entry["content"][:80]  # 最多80字
        lines.append(f"- [{title}] {content_preview}｜关键词：{kw_str}")

    return "\n".join(lines)
