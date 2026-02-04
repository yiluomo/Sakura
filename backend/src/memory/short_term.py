# from collections import defaultdict

# _memory = defaultdict(list)

# def save_turn(user_id:str,user_msg:str,reply:str):
#     _memory[user_id].append({"role":"user","content":user_msg})
#     _memory[user_id].append({"role":"assistant","content":reply})

#     _memory[user_id] = _memory[user_id][-10:]

# def get_recent(user_id,limit=6):
#     return _memory[user_id][-limit:]

from db.database import AsyncSessionLocal
from db.crud import save_conversation, get_recent_conversations

async def save_turn(user_id: str, user_msg: str, reply: str):
    """保存一轮对话"""
    async with AsyncSessionLocal() as db:
        await save_conversation(db, user_id, "user", user_msg)
        await save_conversation(db, user_id, "assistant", reply)

async def get_recent(user_id: str, limit: int = 6):
    """获取最近的对话"""
    async with AsyncSessionLocal() as db:
        return await get_recent_conversations(db, user_id, limit)
