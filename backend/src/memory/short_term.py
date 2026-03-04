from db.database import AsyncSessionLocal
from db.crud import (
    save_conversation,
    get_recent_conversations,
    count_conversations,
    get_oldest_conversations,
    delete_conversations_by_ids,
    save_or_update_long_term_memory,
)
from memory.keyword_extractor import extract_keywords, keywords_to_str
from memory import file_store
from llm.adapter import generate
from config import (
    MEMORY_COMPRESSION_THRESHOLD,
    MEMORY_COMPRESSION_BATCH_SIZE,
    MEMORY_KEEP_RECENT_COUNT
)
from datetime import datetime
import json

async def save_turn(user_id: str, user_msg: str, reply: str):
    """保存一轮对话"""
    async with AsyncSessionLocal() as db:
        await save_conversation(db, user_id, "user", user_msg)
        await save_conversation(db, user_id, "assistant", reply)

    # 自动检查并压缩
    await check_and_compress(user_id)

async def get_recent(user_id: str, limit: int = 6):
    """获取最近的对话"""
    async with AsyncSessionLocal() as db:
        return await get_recent_conversations(db, user_id, limit)

async def get_conversation_count(user_id: str) -> int:
    """获取对话次数"""
    async with AsyncSessionLocal() as db:
        return await count_conversations(db, user_id)

async def summarize_conversations(conversations: list) -> str:
    """使用LLM总结对话内容"""
    # 构建对话文本
    conversation_text = ""
    for conv in conversations:
        role = "用户" if conv["role"] == "user" else "助手"
        conversation_text += f"{role}: {conv['content']}\n"

    # 构建提示词
    prompt = f"""请总结以下对话的关键信息。重点提取：
1. 用户提到的个人信息（姓名、年龄、职业、居住地等）
2. 用户的偏好、兴趣和爱好
3. 用户讨厌或不喜欢的事物
4. 重要的事件、经历或计划
5. 需要记住的特定事实或约定

对话内容：
{conversation_text}

请以简洁的要点形式输出总结，每个要点一行。如果没有重要信息，请回复"无重要信息"。"""

    try:
        summary = await generate(prompt)
        return summary.strip()
    except Exception as e:
        print(f"❌ 对话总结失败: {e}")
        return "对话总结失败"

async def compress_and_archive(
    user_id: str,
    threshold: int = MEMORY_COMPRESSION_THRESHOLD,
    batch_size: int = MEMORY_COMPRESSION_BATCH_SIZE
) -> bool:
    """压缩并归档旧对话到长期记忆"""
    async with AsyncSessionLocal() as db:
        # 1. 检查对话数量
        total_count = await count_conversations(db, user_id)

        if total_count <= threshold:
            return False  # 未达到阈值，不需要压缩

        # 2. 获取最旧的对话
        oldest_conversations = await get_oldest_conversations(db, user_id, batch_size)

        if not oldest_conversations:
            return False

        # 3. 使用LLM总结对话
        summary = await summarize_conversations(oldest_conversations)

        # 4. 写入文件 + 数据库索引（双轨并行）
        if summary and summary != "无重要信息" and summary != "对话总结失败":
            # 生成时间范围作为 key
            start_time = oldest_conversations[0]["timestamp"]
            end_time   = oldest_conversations[-1]["timestamp"]
            time_range = f"{start_time[:10]}_to_{end_time[:10]}"
            memory_type = "conversation_summary"
            importance  = 3

            # 提取关键词
            keywords = await extract_keywords(summary)
            kw_str   = keywords_to_str(keywords)

            # 写入 .md 文件，返回实际写入的文件路径
            rel_path = await file_store.write_entry(
                memory_type, time_range, summary, keywords, importance
            )

            # 写入数据库索引（使用独立 session，避免变量名遮蔽外层 db）
            async with AsyncSessionLocal() as db_index:
                await save_or_update_long_term_memory(
                    db_index, memory_type, time_range, summary,
                    kw_str, rel_path, importance
                )

            print(f"✅ 已压缩 {len(oldest_conversations)} 条对话到长期记忆，关键词: {kw_str}")

        # 5. 删除已压缩的对话
        conversation_ids = [conv["id"] for conv in oldest_conversations]
        await delete_conversations_by_ids(db, conversation_ids)

        return True

async def check_and_compress(user_id: str):
    """检查并触发压缩（如果需要）"""
    try:
        count = await get_conversation_count(user_id)

        if count > MEMORY_COMPRESSION_THRESHOLD:
            print(f"📊 用户 {user_id} 对话数量: {count}, 触发压缩...")
            await compress_and_archive(user_id)
    except Exception as e:
        print(f"❌ 压缩检查失败: {e}")
        # 不影响主流程，继续执行


async def force_archive(user_id: str) -> dict:
    """
    手动强制归档：无视阈值限制，将当前全部短期记忆压缩总结后
    写入长期记忆文件和数据库索引，并清空数据库中的短期对话记录。

    Returns:
        {"success": bool, "msg": str, "archived_count": int}
    """
    try:
        async with AsyncSessionLocal() as db:
            # 获取全部对话记录
            all_conversations = await get_recent_conversations(db, user_id, limit=10000)

        if not all_conversations:
            return {"success": False, "msg": "当前没有可归档的对话记录", "archived_count": 0}

        archived_count = len(all_conversations)

        # 1. LLM 总结
        summary = await summarize_conversations(all_conversations)
        if not summary or summary in ("无重要信息", "对话总结失败"):
            return {"success": False, "msg": f"对话总结失败：{summary}", "archived_count": 0}

        # 2. 生成时间范围 key
        start_time = all_conversations[0]["timestamp"]
        end_time   = all_conversations[-1]["timestamp"]
        time_range = f"{start_time[:10]}_to_{end_time[:10]}"
        memory_type = "conversation_summary"
        importance  = 3

        # 3. 提取关键词
        keywords = await extract_keywords(summary)
        kw_str   = keywords_to_str(keywords)

        # 4. 写入 .md 文件，返回实际写入的文件路径
        rel_path = await file_store.write_entry(memory_type, time_range, summary, keywords, importance)

        # 5. 写入数据库索引
        async with AsyncSessionLocal() as db_index:
            await save_or_update_long_term_memory(
                db_index, memory_type, time_range, summary,
                kw_str, rel_path, importance
            )

        # 6. 清空所有短期对话记录
        async with AsyncSessionLocal() as db:
            conversations_with_ids = await get_oldest_conversations(db, user_id, limit=10000)
            ids_to_delete = [c["id"] for c in conversations_with_ids]
            if ids_to_delete:
                await delete_conversations_by_ids(db, ids_to_delete)

        msg = f"已归档 {archived_count} 条对话，关键词：{kw_str}"
        print(f"✅ [force_archive] {msg}")
        return {"success": True, "msg": msg, "archived_count": archived_count}

    except Exception as e:
        print(f"❌ [force_archive] 归档失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "msg": f"归档失败：{str(e)}", "archived_count": 0}

