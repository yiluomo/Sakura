
def build_prompt(person:str,memory:dict,user_message:str)->str:
    short_term = "\n".join([f"{m['role']}: {m['content']}" for m in memory["short_term"]])
    long_term = memory["long_term"]
    return f"""
{person}
{long_term}
{short_term}
{user_message}

请以八重樱的身份回应
"""