"""
情绪系统核心模块

负责计算和管理用户情绪状态，包括：
- 情感分析（LLM 辅助）
- 敏感话题检测
- mood 值计算（多因素加权）
- 情绪类型判定
- 精力消耗计算
"""

import re
from datetime import datetime
from typing import Dict, Optional
from db.database import get_db_session
from db.crud import get_user_emotion, update_user_emotion
from llm.adapter import generate


# ========== 敏感话题关键词库 ==========

SENSITIVE_TOPICS = {
    "trauma": {  # 创伤性话题
        "keywords": ["凛", "妹妹", "死", "杀", "屠村", "律者", "侵蚀", "封印", "背叛", "牺牲"],
        "severity": -12,
        "emotion_hint": "melancholy"
    },
    "nostalgia": {  # 怀念性话题
        "keywords": ["卡莲", "八重村", "五百年", "过去", "以前", "那时", "还记得", "曾经"],
        "severity": 0,  # 不降低 mood，但触发怀念情绪
        "emotion_hint": "nostalgic"
    },
    "beauty": {  # 美好事物
        "keywords": ["樱花", "守护", "承诺", "陪伴", "温暖", "美好"],
        "severity": 8,
        "emotion_hint": "happy"
    }
}


# ========== 情感分析 ==========

async def analyze_message_sentiment(message: str) -> int:
    """
    用 LLM 分析用户消息的情感倾向
    返回：-10 到 +10 的情感分数
    """
    prompt = f"""分析以下消息的情感倾向，返回一个 -10 到 +10 的数字：
- 负数表示消极、冷漠、攻击性
- 正数表示积极、温暖、关心
- 0 表示中性

只返回数字，不要任何解释。

消息：{message}

情感分数："""

    try:
        response = await generate(prompt)
        # 提取数字
        match = re.search(r'-?\d+', response.strip())
        if match:
            score = int(match.group())
            return max(-10, min(10, score))  # 限制范围
        return 0
    except Exception as e:
        print(f"⚠️  [Emotion] 情感分析失败: {e}")
        return 0


# ========== 敏感话题检测 ==========

def detect_sensitive_topics(message: str) -> Dict:
    """
    检测敏感话题关键词
    返回：{"has_sensitive": bool, "topics": [...], "severity": int, "emotion_hint": str}
    """
    detected_topics = []
    total_severity = 0
    emotion_hints = []

    for topic_name, topic_data in SENSITIVE_TOPICS.items():
        for keyword in topic_data["keywords"]:
            if keyword in message:
                detected_topics.append(topic_name)
                total_severity += topic_data["severity"]
                if topic_data["emotion_hint"]:
                    emotion_hints.append(topic_data["emotion_hint"])
                break  # 每个主题只计算一次

    return {
        "has_sensitive": len(detected_topics) > 0,
        "topics": detected_topics,
        "severity": total_severity,
        "emotion_hint": emotion_hints[0] if emotion_hints else None
    }


# ========== mood 值计算 ==========

async def calculate_mood_change(
    user_id: str,
    message: str,
    current_mood: int,
    current_affinity: int,
    time_gap_hours: float
) -> int:
    """
    综合计算 mood 变化值
    返回：新的 mood 值 (0-100)
    """
    mood_delta = 0

    # 1. 情感分析（LLM 辅助）
    sentiment_score = await analyze_message_sentiment(message)
    mood_delta += sentiment_score

    # 2. 敏感话题检测
    sensitive = detect_sensitive_topics(message)
    mood_delta += sensitive["severity"]

    # 3. 时间因素
    if time_gap_hours < 0.083:  # < 5分钟
        mood_delta += 1  # 连续对话，陪伴感
    elif 6 <= time_gap_hours <= 24:
        mood_delta += 0  # 正常
    elif 24 < time_gap_hours <= 72:
        mood_delta -= 3  # 轻微孤独
    elif 72 < time_gap_hours <= 168:
        mood_delta -= 8  # 被遗忘感
    elif time_gap_hours > 168:
        mood_delta -= 15  # 深度孤独

    # 4. 亲密度影响
    if current_affinity < 20:
        # 低亲密度：mood 上限 60
        new_mood = min(60, current_mood + mood_delta)
    elif current_affinity > 50:
        # 高亲密度：负面情绪衰减加快，正面情绪增强
        if mood_delta > 0:
            mood_delta = int(mood_delta * 1.2)
        elif mood_delta < 0:
            mood_delta = int(mood_delta * 0.8)
        new_mood = current_mood + mood_delta
    else:
        new_mood = current_mood + mood_delta

    # 限制范围 0-100
    return max(0, min(100, new_mood))


# ========== 精力消耗计算 ==========

def calculate_energy_cost(message: str, emotion_type: str) -> int:
    """
    计算本次对话的精力消耗
    返回：消耗的 energy 值
    """
    cost = 1  # 基础消耗

    # 根据消息长度
    if len(message) > 100:
        cost += 5
    elif len(message) > 50:
        cost += 2

    # 根据情绪类型
    if emotion_type == "melancholy":
        cost += 8  # 情绪化对话消耗大
    elif emotion_type == "guarded":
        cost += 5

    # 检测敏感话题
    sensitive = detect_sensitive_topics(message)
    if "trauma" in sensitive["topics"]:
        cost += 8

    return cost


# ========== 情绪类型判定 ==========

def determine_emotion_type(
    mood: int,
    energy: int,
    sensitive_topics: Dict,
    current_emotion: str = "calm"
) -> str:
    """
    根据 mood、energy 和上下文判定情绪类型
    返回：calm/happy/melancholy/nostalgic/guarded
    
    优先级规则（从高到低）：
    1. guarded（警戒）
    2. melancholy（忧郁）
    3. nostalgic（怀念）
    4. happy（愉悦）
    5. calm（平静）
    """
    
    # 1. guarded（警戒）- 暂时通过外部触发，此处预留
    # 未来可以通过 LLM 分析用户是否质疑/冒犯
    
    # 2. melancholy（忧郁）
    if "trauma" in sensitive_topics.get("topics", []):
        return "melancholy"
    if mood < 35:
        return "melancholy"
    if energy < 25 and mood < 50:
        return "melancholy"
    
    # 3. nostalgic（怀念）
    if "nostalgia" in sensitive_topics.get("topics", []):
        return "nostalgic"
    
    # 4. happy（愉悦）
    if mood > 65:
        return "happy"
    if "beauty" in sensitive_topics.get("topics", []):
        return "happy"
    
    # 5. calm（平静）- 默认状态
    return "calm"


# ========== 情绪衰减（预留给定时任务） ==========

def apply_emotion_decay(mood: int, emotion_type: str) -> tuple[int, str]:
    """
    应用情绪自然衰减
    返回：(新 mood 值, 新情绪类型)
    
    注意：此函数预留给定时任务调用，当前版本暂不使用
    """
    new_mood = mood
    new_emotion = emotion_type
    
    # melancholy → calm：每轮 +5 mood
    if emotion_type == "melancholy" and mood < 45:
        new_mood = min(50, mood + 5)
        if new_mood >= 45:
            new_emotion = "calm"
    
    # happy → calm：mood 自然衰减 -2
    elif emotion_type == "happy" and mood > 60:
        new_mood = max(50, mood - 2)
        if new_mood <= 60:
            new_emotion = "calm"
    
    # nostalgic/guarded → calm：话题结束后自然恢复
    elif emotion_type in ["nostalgic", "guarded"]:
        new_emotion = "calm"
    
    return new_mood, new_emotion


# ========== 主入口：更新情绪状态 ==========

async def update_emotion_state(user_id: str, message: str) -> Dict:
    """
    主入口：更新用户情绪状态
    返回：{"emotion_type": str, "mood": int, "energy": int}
    """
    async with get_db_session() as db:
        # 1. 获取当前状态
        current_state = await get_user_emotion(db, user_id)
        current_mood = current_state["mood"]
        current_energy = current_state["energy"]
        current_affinity = current_state["affinity"]
        current_emotion = current_state["emotion_type"]
        last_interaction = current_state["last_interaction"]
        
        # 2. 计算时间间隔
        now = datetime.now()
        if last_interaction is None:
            last_interaction = now
        time_gap = (now - last_interaction).total_seconds() / 3600  # 小时
        
        # 3. 检测敏感话题
        sensitive = detect_sensitive_topics(message)
        
        # 4. 计算 mood 变化
        new_mood = await calculate_mood_change(
            user_id, message, current_mood, current_affinity, time_gap
        )
        
        # 5. 判定情绪类型
        new_emotion = determine_emotion_type(
            new_mood, current_energy, sensitive, current_emotion
        )
        
        # 6. 计算 energy 消耗
        energy_cost = calculate_energy_cost(message, new_emotion)
        new_energy = max(0, current_energy - energy_cost)
        
        # 7. 更新数据库
        await update_user_emotion(db, user_id, new_emotion, new_mood, new_energy)
        
        return {
            "emotion_type": new_emotion,
            "mood": new_mood,
            "energy": new_energy
        }


# ========== 精力恢复（预留给定时任务） ==========

async def recover_energy(user_id: str, hours: float = 1.0):
    """
    精力自然恢复
    每小时恢复 5 点
    
    注意：此函数预留给定时任务调用，当前版本暂不使用
    """
    async with get_db_session() as db:
        current_state = await get_user_emotion(db, user_id)
        current_energy = current_state["energy"]
        
        recovery = int(5 * hours)
        new_energy = min(100, current_energy + recovery)
        
        await update_user_emotion(
            db, user_id,
            current_state["emotion_type"],
            current_state["mood"],
            new_energy
        )
