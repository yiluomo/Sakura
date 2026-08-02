from llm.llmModel.dpsk import call_deepseek

import traceback

async def generate(prompt: str) -> str:
    try:
        return await call_deepseek(prompt)
    except Exception as e:
        print(f"❌ 模型调用失败: {e}")
        traceback.print_exc()
        # 返回备用回复，避免整个服务崩溃
        return "抱歉，我现在有些不舒服，请稍后再试..."

    # return "舰长，我一直都在，我可以听到你"
