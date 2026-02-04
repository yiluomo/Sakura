import httpx 

DeepSeek_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
API_KEY = "sk-662cc6ddd16c46369fe799dea0855625"


async def call_deepseek(prompt:str)->str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            DeepSeek_URL, 
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
            "model": MODEL_NAME,
            # "prompt": prompt,
            # "stream": False
            "messages": [
                    {"role": "user", "content": prompt}
                ],
            "temperature": 0.7
        })
        response.raise_for_status()
        # return response.json()["response"]
        return response.json()["choices"][0]["message"]["content"]