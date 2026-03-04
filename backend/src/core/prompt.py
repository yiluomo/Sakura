
# TTS 输出格式约束
# 放在 prompt 末尾，紧贴指令，对模型约束力最强
TTS_OUTPUT_RULES = """
【回复格式要求】
1. 句子要简短，多用逗号，省略号，顿号分隔，制造自然停顿，适合语音朗读。
2. 语气温和、流畅，有情绪起伏，不要生硬。
3. 不使用任何特殊格式、符号、表情，只使用标准中文标点（。，？！…—）。
"""


def build_prompt(person: str, memory: dict, user_message: str) -> str:
    short_term = "\n".join([f"{m['role']}: {m['content']}" for m in memory["short_term"]])
    long_term  = memory["long_term"]

    # 长期记忆存在时才注入，避免空段落干扰
    long_term_section = f"【关于此人你记得的事】\n{long_term}\n" if long_term.strip() else ""

    return f"""{person}

{long_term_section}【近期对话记录】
{short_term}

【用户当前消息】
{user_message}

现在，以八重樱的身份，用她的语气和风格，自然地回应这条消息。
{TTS_OUTPUT_RULES}"""

