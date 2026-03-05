
# 情绪语气映射
EMOTION_TONE_MAP = {
    "calm": "以八重樱的身份，用她沉静克制的语气，自然地回应这条消息。",
    "happy": "以八重樱的身份回应。此刻心情不错，语气可以稍微温和轻松一些，但依然保持她的克制。",
    "melancholy": "以八重樱的身份回应。此刻有些沉默，不太想多说话，回复简短一些。多用省略号。",
    "nostalgic": "以八重樱的身份回应。此刻想起了过去的事，语气带着回忆的感觉，说话会慢一些。",
    "guarded": "以八重樱的身份回应。此刻保持警戒，语气冷静克制，保持距离感。"
}

# TTS 输出格式约束
# 放在 prompt 末尾，紧贴指令，对模型约束力最强
TTS_OUTPUT_RULES = """
【回复格式要求】
1. 句子简短，多用逗号、省略号、顿号分隔，制造自然停顿，适合语音朗读。
2. 语气温和流畅，有情绪起伏，不要生硬。
3. 只使用标准中文标点（。，？！…—），不使用任何特殊符号、表情、格式标记。
4. 不要添加动作描述、心理活动、旁白等非语音内容。
"""


def build_prompt(
    person: str,
    memory: dict,
    user_message: str,
    emotion_type: str = "calm",
    mood: int = 50,
    energy: int = 80
) -> str:
    """
    构建提示词，注入情绪状态
    
    参数：
        person: 人格描述
        memory: 记忆上下文
        user_message: 用户消息
        emotion_type: 情绪类型
        mood: 心情值 0-100
        energy: 精力值 0-100
    """
    short_term = "\n".join([f"{m['role']}: {m['content']}" for m in memory["short_term"]])
    long_term  = memory["long_term"]

    # 长期记忆存在时才注入，避免空段落干扰
    long_term_section = f"【关于此人你记得的事】\n{long_term}\n" if long_term.strip() else ""

    # 根据情绪类型选择语气描述
    tone_instruction = EMOTION_TONE_MAP.get(emotion_type, EMOTION_TONE_MAP["calm"])
    
    # 根据精力值调整回复长度提示
    length_hint = ""
    if energy < 30:
        length_hint = "你现在有些疲惫，回复尽量简短。"
    elif energy > 70 and mood > 60:
        length_hint = "你现在状态不错，可以多说一些。"

    return f"""{person}

{long_term_section}【近期对话记录】
{short_term}

【用户当前消息】
{user_message}

{tone_instruction}
{length_hint}
{TTS_OUTPUT_RULES}"""

