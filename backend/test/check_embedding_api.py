"""
检查 Embedding API 配置
"""
import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openai import AsyncOpenAI
from config import (
    EMBEDDING_API_KEY,
    EMBEDDING_API_BASE,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
)


async def test_embedding_api():
    """测试 Embedding API 是否可用"""
    print("=" * 60)
    print("Embedding API 配置检查")
    print("=" * 60)
    
    print(f"\n当前配置:")
    print(f"  API Base: {EMBEDDING_API_BASE}")
    print(f"  API Key: {EMBEDDING_API_KEY[:20]}..." if len(EMBEDDING_API_KEY) > 20 else f"  API Key: {EMBEDDING_API_KEY}")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Dimension: {EMBEDDING_DIMENSION}")
    
    print("\n" + "-" * 60)
    print("测试 API 连接...")
    print("-" * 60)
    
    try:
        client = AsyncOpenAI(
            api_key=EMBEDDING_API_KEY,
            base_url=EMBEDDING_API_BASE,
        )
        
        test_text = "这是一个测试文本"
        print(f"\n发送测试请求: '{test_text}'")
        
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=test_text,
        )
        
        embedding = response.data[0].embedding
        print(f"\n✅ API 连接成功!")
        print(f"  返回向量维度: {len(embedding)}")
        print(f"  向量前5个值: {embedding[:5]}")
        
        if len(embedding) != EMBEDDING_DIMENSION:
            print(f"\n⚠️  警告: 返回的向量维度 ({len(embedding)}) 与配置不符 ({EMBEDDING_DIMENSION})")
            print(f"  建议修改 config.py 中的 EMBEDDING_DIMENSION = {len(embedding)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API 连接失败: {e}")
        print("\n可能的原因:")
        print("  1. DeepSeek API 不支持 embedding 模型")
        print("  2. API Key 或 Base URL 配置错误")
        print("  3. 模型名称不正确")
        
        print("\n解决方案:")
        print("  方案1: 使用 OpenAI API")
        print("    - 在 config.py 中设置:")
        print("      EMBEDDING_API_KEY = 'your-openai-api-key'")
        print("      EMBEDDING_API_BASE = 'https://api.openai.com/v1'")
        print("      EMBEDDING_MODEL = 'text-embedding-3-small'")
        print("      EMBEDDING_DIMENSION = 1536")
        
        print("\n  方案2: 使用兼容的第三方服务")
        print("    - 硅基流动 (https://siliconflow.cn)")
        print("      EMBEDDING_API_BASE = 'https://api.siliconflow.cn/v1'")
        print("      EMBEDDING_MODEL = 'BAAI/bge-large-zh-v1.5'")
        print("      EMBEDDING_DIMENSION = 1024")
        
        print("\n  方案3: 使用本地 Embedding 模型")
        print("    - 需要修改 vector_store.py 使用本地模型（如 sentence-transformers）")
        
        return False


async def main():
    success = await test_embedding_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 配置检查通过，可以运行 RAG 测试")
    else:
        print("✗ 配置检查失败，请修复后再运行 RAG 测试")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
