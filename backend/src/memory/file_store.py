"""
file_store.py
长期记忆文件存储模块。
负责将记忆内容以 Markdown 格式写入 memory_store/ 目录下的对应文件。
数据库作为轻量索引，文件存储完整可读内容。

对话摘要（conversation_summary）的存储规则：
  - 文件命名：summaries_1.md、summaries_2.md……
  - 每个文件最多存 SUMMARIES_MAX_ENTRIES 条记录（默认 10 条）
  - 写新摘要时，自动找当前未满的最新文件，满了则新建下一个
  - 写入函数返回实际使用的文件路径，供调用方写入数据库索引

归档对话（archived_conversation）的存储规则：
  - 文件命名：archived_1.md、archived_2.md……
  - 每个文件最多存 ARCHIVE_MAX_ENTRIES 条记录（默认 50 条）
  - 保留对话原文、角色、情绪、关键词等完整字段
  - 向量文件丢失时可从此文件恢复
"""

import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import aiofiles

from config import MEMORY_STORE_DIR


# ─────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────

# 每个 summaries_N.md 文件最多存储的摘要条数
SUMMARIES_MAX_ENTRIES = 10

# 每个 archived_N.md 文件最多存储的归档对话条数
ARCHIVE_MAX_ENTRIES = 50


# ─────────────────────────────────────────────
# 全局写锁（单用户，串行化所有写操作）
# ─────────────────────────────────────────────
_write_lock = asyncio.Lock()


# ─────────────────────────────────────────────
# memory_type → 文件名 映射（不含 summaries，动态处理）
# ─────────────────────────────────────────────
_TYPE_TO_FILE = {
    "name":         "profile.md",
    "age":          "profile.md",
    "birthday":     "profile.md",
    "location":     "profile.md",
    "occupation":   "profile.md",
    "family":       "profile.md",
    "friend":       "profile.md",
    "hobby":        "preferences.md",
    "dislike":      "preferences.md",
    "experience":   "preferences.md",
    "manual":       "notes.md",
    # conversation_summary 不在此表中，由 _get_summary_target_file() 动态确定
}

# 固定文件的标题
_FILE_TITLES = {
    "profile.md":     "# 个人档案",
    "preferences.md": "# 偏好与经历",
    "notes.md":       "# 手动笔记",
}

# memory_type → 可读中文标题
_TYPE_TO_TITLE = {
    "name":                   "姓名",
    "age":                    "年龄",
    "birthday":               "生日",
    "location":               "居住地",
    "occupation":             "职业",
    "family":                 "家人",
    "friend":                 "朋友",
    "hobby":                  "爱好",
    "dislike":                "厌恶",
    "experience":             "经历",
    "manual":                 "备忘",
    "conversation_summary":   "对话摘要",
    "archived_conversation":  "归档对话",
}


# ─────────────────────────────────────────────
# 通用文件系列管理工具
# ─────────────────────────────────────────────

def _get_all_series_files(prefix: str) -> List[Path]:
    """
    返回所有 {prefix}_N.md 文件，按编号从小到大排列。
    例：prefix="summaries" → summaries_1.md, summaries_2.md ...
    """
    files = []
    for fp in MEMORY_STORE_DIR.glob(f"{prefix}_*.md"):
        m = re.search(rf"{re.escape(prefix)}_(\d+)\.md$", fp.name)
        if m:
            files.append((int(m.group(1)), fp))
    return [fp for _, fp in sorted(files)]


def _count_file_entries(filepath: Path) -> int:
    """同步统计文件中的条目数（通过计数 <!-- entry: 标记）。"""
    if not filepath.exists():
        return 0
    with open(filepath, encoding="utf-8") as f:
        return f.read().count("<!-- entry:")


def _find_key_in_series(prefix: str, memory_type: str, key: str) -> Optional[Path]:
    """
    在所有 {prefix}_N.md 文件中查找指定 key 是否已存在。
    返回包含该 key 的文件路径，未找到返回 None。
    """
    marker = f"<!-- entry: {memory_type}/{key} -->"
    for fp in _get_all_series_files(prefix):
        if not fp.exists():
            continue
        with open(fp, encoding="utf-8") as f:
            if marker in f.read():
                return fp
    return None


def _get_series_target_file(prefix: str, memory_type: str, key: str, max_entries: int) -> Path:
    """
    为新条目确定目标文件：
    - 若 key 已存在于某文件 → 返回该文件（原地更新）
    - 否则找最新的未满文件（< max_entries 条）→ 返回该文件
    - 若所有文件都满 → 新建 {prefix}_(N+1).md
    """
    existing = _find_key_in_series(prefix, memory_type, key)
    if existing:
        return existing

    all_files = _get_all_series_files(prefix)
    for fp in reversed(all_files):
        if _count_file_entries(fp) < max_entries:
            return fp

    next_num = len(all_files) + 1
    return MEMORY_STORE_DIR / f"{prefix}_{next_num}.md"


# ─────────────────────────────────────────────
# 摘要文件管理（summaries_N.md 系列）
# ─────────────────────────────────────────────

def _get_all_summary_files() -> List[Path]:
    """返回所有 summaries_N.md 文件，按编号从小到大排列。"""
    return _get_all_series_files("summaries")


def _get_summary_target_file(key: str) -> Path:
    """为新摘要确定目标文件（见 _get_series_target_file）。"""
    return _get_series_target_file("summaries", "conversation_summary", key, SUMMARIES_MAX_ENTRIES)


# ─────────────────────────────────────────────
# 归档文件管理（archived_N.md 系列）
# ─────────────────────────────────────────────

def _get_all_archive_files() -> List[Path]:
    """返回所有 archived_N.md 文件，按编号从小到大排列。"""
    return _get_all_series_files("archived")


def _get_archive_target_file(key: str) -> Path:
    """为新归档对话确定目标文件（见 _get_series_target_file）。"""
    return _get_series_target_file("archived", "archived_conversation", key, ARCHIVE_MAX_ENTRIES)


# ─────────────────────────────────────────────
# 路径工具
# ─────────────────────────────────────────────

def get_target_file(memory_type: str, key: str = "") -> Path:
    """
    根据 memory_type 返回对应 .md 文件的绝对路径。
    对动态文件系列（conversation_summary / archived_conversation）需要传入 key。
    """
    if memory_type == "conversation_summary":
        return _get_summary_target_file(key)
    if memory_type == "archived_conversation":
        return _get_archive_target_file(key)
    filename = _TYPE_TO_FILE.get(memory_type, "notes.md")
    return MEMORY_STORE_DIR / filename


def get_relative_path(memory_type: str, key: str = "") -> str:
    """
    返回相对路径字符串，用于写入数据库 file_path 字段。
    """
    filepath = get_target_file(memory_type, key)
    return f"memory_store/{filepath.name}"


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
    构建普通记忆条目块（profile / preferences / notes）。
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
    构建对话摘要专用条目块（summaries_N.md 格式，内容较长）。
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


def _build_archive_entry_block(
    key: str,
    role: str,
    content: str,
    keywords: List[str],
    emotion_type: str = "calm",
    importance: int = 3,
    timestamp: str = "",
) -> str:
    """
    构建归档对话专用条目块（archived_N.md 格式）。
    保留完整原文、角色、情绪、关键词，用于向量文件丢失时恢复。
    """
    kw_str = " ".join([f"`{kw}`" for kw in keywords]) if keywords else "（无）"
    role_label = "会话" if role == "session" else ("用户" if role == "user" else "樱")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ts_str = f"  \n**时间范围**：{timestamp}" if role == "session" and timestamp else (f"  \n**原始时间**：{timestamp}" if timestamp else "")

    return (
        f"\n<!-- entry: archived_conversation/{key} -->\n"
        f"## 归档对话 [{role_label}]\n"
        f"**内容**：{content}  \n"
        f"**情绪**：{emotion_type}  \n"
        f"**关键词**：{kw_str}  \n"
        f"**重要度**：{importance}{ts_str}  \n"
        f"**归档时间**：{now}\n\n"
        f"---\n"
    )


# ─────────────────────────────────────────────
# 核心写入函数
# ─────────────────────────────────────────────

async def write_entry(
    memory_type: str,
    key: str,
    content: str,
    keywords: List[str],
    importance: int = 3,
    # 归档对话专用字段（archived_conversation 类型时使用）
    role: str = "",
    emotion_type: str = "calm",
    timestamp: str = "",
) -> str:
    """
    写入或更新单条记忆到对应的 .md 文件。

    - 对 conversation_summary：自动路由到正确的 summaries_N.md
    - 对 archived_conversation：自动路由到正确的 archived_N.md
    - 其他类型：写入固定对应文件
    - 找到已有 <!-- entry: type/key --> 注释 → 替换整个条目块
    - 未找到 → 追加到文件末尾
    - 使用全局写锁保障并发安全

    Returns:
        实际写入的文件相对路径（用于写入数据库 file_path 字段）
    """
    filepath = get_target_file(memory_type, key)

    # 构建新的条目文本
    if memory_type == "conversation_summary":
        new_block = _build_summary_entry_block(key, content, keywords)
        file_title = f"# 对话摘要记录（{filepath.stem.replace('summaries_', '第')}卷）"
    elif memory_type == "archived_conversation":
        new_block = _build_archive_entry_block(
            key, role, content, keywords, emotion_type, importance, timestamp
        )
        vol_num = filepath.stem.replace("archived_", "第")
        file_title = f"# 归档对话记录（{vol_num}卷）"
    else:
        new_block = _build_entry_block(memory_type, key, content, keywords, importance)
        filename = _TYPE_TO_FILE.get(memory_type, "notes.md")
        file_title = _FILE_TITLES.get(filename, "# 记忆")

    async with _write_lock:
        existing = await _read_file(filepath)

        # 文件为空或不存在时，添加文件标题头
        if not existing.strip():
            existing = f"{file_title}\n"

        # 用正则定位 <!-- entry: type/key --> 到下一个 entry 或文件末尾
        pattern = re.compile(
            r'\n<!-- entry: ' + re.escape(f"{memory_type}/{key}") + r' -->.*?(?=\n<!-- entry:|\Z)',
            re.DOTALL
        )

        if pattern.search(existing):
            updated = pattern.sub(new_block, existing)
        else:
            updated = existing.rstrip() + "\n" + new_block

        await _write_file(filepath, updated)

    return f"memory_store/{filepath.name}"


# ─────────────────────────────────────────────
# 读取用于 prompt 注入
# ─────────────────────────────────────────────

def _parse_entries_from_file(text: str) -> List[dict]:
    """
    从文件文本中解析所有条目，提取 memory_type、key、content、keywords、importance。
    """
    entries = []
    pattern = re.compile(
        r'<!-- entry: (\w+)/(.+?) -->\n'   # type / key
        r'## .+?\n'                         # 标题行
        r'(.*?)'                            # 条目内容（非贪婪）
        r'(?=\n<!-- entry:|\Z)',            # 到下一个条目或文件末尾
        re.DOTALL
    )
    for m in pattern.finditer(text):
        memory_type = m.group(1)
        key = m.group(2).strip()
        body = m.group(3)

        # 提取 **内容** 或 **摘要**
        content_match = re.search(r'\*\*(?:内容|摘要)\*\*[：:]\s*(.+?)(?=\n\*\*|\n\n---|  \n\*\*|\Z)', body, re.DOTALL)
        content = content_match.group(1).strip() if content_match else ""

        # 提取 **关键词**
        kw_match = re.search(r'\*\*关键词\*\*[：:]\s*(.+?)(?:  \n|\n)', body)
        kw_raw = kw_match.group(1).strip() if kw_match else ""
        keywords = [k.strip('`') for k in kw_raw.split() if k.strip('`')]

        # 提取 **重要度**（summaries 默认重要度 3）
        imp_match = re.search(r'\*\*重要度\*\*[：:]\s*(\d+)', body)
        importance = int(imp_match.group(1)) if imp_match else 3

        entries.append({
            "memory_type": memory_type,
            "key":         key,
            "content":     content,
            "keywords":    keywords,
            "importance":  importance,
        })

    return entries


async def get_top_memories(n: int = 5) -> str:
    """
    读取所有 .md 文件，解析条目，按重要度降序取前 n 条。
    summaries / archived 系列会读取全部卷。
    返回格式化的字符串，用于注入对话 prompt。
    """
    all_entries = []

    # 读取固定文件
    for filename in ["profile.md", "preferences.md", "notes.md"]:
        filepath = MEMORY_STORE_DIR / filename
        text = await _read_file(filepath)
        if text:
            all_entries.extend(_parse_entries_from_file(text))

    # 读取所有 summaries_N.md 文件
    for fp in _get_all_summary_files():
        text = await _read_file(fp)
        if text:
            all_entries.extend(_parse_entries_from_file(text))

    # 读取所有 archived_N.md 文件（归档的原始对话）
    for fp in _get_all_archive_files():
        text = await _read_file(fp)
        if text:
            all_entries.extend(_parse_entries_from_file(text))

    if not all_entries:
        return ""

    # 按重要度降序，取前 n 条
    top = sorted(all_entries, key=lambda e: e["importance"], reverse=True)[:n]

    lines = ["【用户长期记忆】"]
    for entry in top:
        title = _TYPE_TO_TITLE.get(entry["memory_type"], entry["memory_type"])
        kw_str = "、".join(entry["keywords"]) if entry["keywords"] else "无"
        content_preview = entry["content"][:80]
        lines.append(f"- [{title}] {content_preview}｜关键词：{kw_str}")

    return "\n".join(lines)


async def delete_entry(memory_type: str, key: str) -> bool:
    """
    从对应的 .md 文件中删除特定的条目块。
    """
    filepath = get_target_file(memory_type, key)
    if not filepath.exists():
        return False

    async with _write_lock:
        existing = await _read_file(filepath)
        if not existing.strip():
            return False

        # 用正则定位 <!-- entry: type/key --> 到下一个 entry 或文件末尾
        pattern = re.compile(
            r'\n*<!-- entry: ' + re.escape(f"{memory_type}/{key}") + r' -->.*?(?=\n*<!-- entry:|\Z)',
            re.DOTALL
        )

        if pattern.search(existing):
            updated = pattern.sub("", existing)
            # 清理可能产生的多个连续换行，并确保末尾只有一个换行
            updated = re.sub(r'\n{3,}', '\n\n', updated)
            await _write_file(filepath, updated.strip() + "\n")
            return True
        return False

