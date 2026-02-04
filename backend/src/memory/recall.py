from memory.short_term import get_recent
from memory.long_term import get_profile

async def recall_context(user_id:str)->dict:
    return {
        "short_term": await get_recent(user_id),
        "long_term": await get_profile(user_id)
    }