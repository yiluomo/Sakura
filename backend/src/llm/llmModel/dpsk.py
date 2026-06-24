import httpx 
import config

async def call_deepseek(prompt:str)->str:
    url = f"{config.LLM_API_BASE.rstrip('/')}/chat/completions"
    api_key = config.LLM_API_KEY
    model = config.LLM_MODEL

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url, 
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]