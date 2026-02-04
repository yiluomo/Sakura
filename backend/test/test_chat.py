import httpx
import asyncio

async def chat_loop():
    url = "http://localhost:8000/api/chat"
    user_id = "依洛沐"
    
    print("===樱对话测试===")
    print("输入'exit'退出\n")

    while True:
        try:
            message = input("你：")
        except EOFError:
            break
            
        if message.lower() == 'exit':
            break
        
        if not message.strip():
            continue
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url, 
                    json={'user_id': user_id, 'message': message}
                )
                response.raise_for_status()
                reply = response.json()["reply"]
                print(f"八重樱：{reply}\n")
        except httpx.HTTPStatusError as e:
            print(f"[错误] HTTP {e.response.status_code}: {e.response.text}\n")
        except httpx.RequestError as e:
            print(f"[错误] 请求失败: {e}\n")
        except KeyError:
            print(f"[错误] 响应格式错误\n")
        except Exception as e:
            print(f"[错误] {e}\n")

if __name__ == '__main__':
    asyncio.run(chat_loop())
