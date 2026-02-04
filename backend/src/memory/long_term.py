# _profiles = {}

# def maybe_save_long_term(user_id:str,user_msg:str,reply:str):
#     if user_msg.startswith("记住"):
#         _profiles[user_id] = user_msg[2:]

# def get_profile(user_id:str)->str:
#     return _profiles.get(user_id,[])

from db.database import AsyncSessionLocal
from db.crud import save_long_term_memory, get_long_term_memories, check_memory_exists
from datetime import datetime
from typing import Optional, Dict

async def save_memory(user_id: str, content: str):
    """手动保存长期记忆"""
    async with AsyncSessionLocal() as db:
        await save_long_term_memory(
            db, user_id, "manual", "user_note", content, importance=5
        )

async def check_memory_trigger(user_id: str, user_msg: str) -> Optional[Dict]:
    """检查是否触发记忆保存，返回记忆信息用于前端确认（不影响对话流程）"""
    
    # 1. 检测"记住"关键词
    if user_msg.startswith("记住"):
        content = user_msg[2:].strip()
        
        # 2. 智能分类：检测记忆类型
        memory_info = _detect_memory_type(content)
        
        if memory_info:
            # 3. 检查是否已存在
            async with AsyncSessionLocal() as db:
                existing = await check_memory_exists(
                    db, user_id, memory_info["type"], memory_info["key"]
                )
                
                if existing:
                    # 已存在，返回信息让前端确认是否更新
                    return {
                        "action": "update",
                        "memory_type": memory_info["type"],
                        "key": memory_info["key"],
                        "old_value": existing.value,
                        "new_value": content,
                        "importance": memory_info["importance"]
                    }
                else:
                    # 不存在，返回信息让前端确认是否保存
                    return {
                        "action": "create",
                        "memory_type": memory_info["type"],
                        "key": memory_info["key"],
                        "value": content,
                        "importance": memory_info["importance"]
                    }
        else:
            # 未检测到具体类型，作为通用记忆
            return {
                "action": "create",
                "memory_type": "manual",
                "key": "user_note",
                "value": content,
                "importance": 3
            }
    
    return None

def _detect_memory_type(content: str) -> Optional[Dict]:
    """检测记忆类型和关键词"""
    
    # 定义关键词映射
    keywords_map = {
        # 名字相关
        "name": {
            "keywords": ["我叫", "我的名字", "叫我", "我是"],
            "importance": 5
        },
        # 爱好相关
        "hobby": {
            "keywords": ["我喜欢", "我爱", "我的爱好", "我喜爱"],
            "importance": 4
        },
        "dislike": {
            "keywords": ["我讨厌", "我不喜欢", "我厌恶"],
            "importance": 4
        },
        # 家人相关
        "family": {
            "keywords": ["我的家人", "我的父母", "我的爸爸", "我的妈妈", "我的兄弟", "我的姐妹"],
            "importance": 5
        },
        # 朋友相关
        "friend": {
            "keywords": ["我的朋友", "我的好友"],
            "importance": 4
        },
        # 生日相关
        "birthday": {
            "keywords": ["我的生日", "我生日", "我出生"],
            "importance": 5
        },
        # 年龄相关
        "age": {
            "keywords": ["我今年", "我的年龄", "我多大"],
            "importance": 4
        },
        # 居住地相关
        "location": {
            "keywords": ["我住在", "我来自", "我在", "我的家乡"],
            "importance": 4
        },
        # 职业相关
        "occupation": {
            "keywords": ["我的工作", "我是", "我做", "我的职业"],
            "importance": 4
        },
        # 经历相关
        "experience": {
            "keywords": ["我曾经", "我以前", "我经历过"],
            "importance": 3
        }
    }
    
    # 检测关键词
    for memory_type, info in keywords_map.items():
        for keyword in info["keywords"]:
            if keyword in content:
                return {
                    "type": memory_type,
                    "key": keyword,
                    "importance": info["importance"]
                }
    
    return None

async def confirm_save_memory(user_id: str, memory_info: Dict) -> bool:
    """确认保存记忆到数据库"""
    async with AsyncSessionLocal() as db:
        if memory_info["action"] == "update":
            # 更新现有记忆
            existing = await check_memory_exists(
                db, user_id, memory_info["memory_type"], memory_info["key"]
            )
            if existing:
                existing.value = memory_info["new_value"]
                existing.importance = memory_info["importance"]
                existing.updated_at = datetime.now()
                await db.commit()
                return True
        else:
            # 创建新记忆
            await save_long_term_memory(
                db,
                user_id,
                memory_info["memory_type"],
                memory_info["key"],
                memory_info["value"],
                memory_info["importance"]
            )
            return True
    return False
    

async def get_profile(user_id: str) -> str:
    """获取用户档案"""
    async with AsyncSessionLocal() as db:
        memories = await get_long_term_memories(db, user_id)
        if memories:
            sorted_memories = sorted(memories, key=lambda m: m.importance, reverse=True)[:5]
            return "\n".join([f"[{m.memory_type}] {m.value}" for m in sorted_memories])
        return ""
