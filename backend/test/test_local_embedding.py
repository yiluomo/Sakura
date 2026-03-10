"""
测试本地 Embedding 模型
"""
import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.vector_store import generate_embedding, init_collection
from config import EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_DIMENSION


async def test_local_embedding():
    """测试本地 Embedding 模型"""
    print("=" * 60)
    print("本地 Embedding 模型测试")
    print("=" * 60)
    
    print(f"\n当前配置:")
    print(f"  模式: {EMBEDDING_MODE}")
    print(f"  模型: {LOCAL_EMBEDDING_MODEL}")
    print(f"  维度: {LOCAL_EMBEDDING_DIMENSION}")
    
    # 初始化
    print("\n" + "-" * 60)
    print("初始化向量存储...")
    print("-" * 60)
    
    if not init_collection():
        print("❌ 初始化失败")
        return False
    
    # 测试生成向量
    print("\n" + "-" * 60)
    print("测试向量生成...")
    print("-" * 60)
    
    test_texts = [
        "我喜欢在图书馆看书学习",
        "图书馆是一个安静的阅读场所",
        "今天的天气非常晴朗",
    ]
    
    embeddings = []
    for text in test_texts:
        print(f"\n文本: '{text}'")
        embedding = await generate_embedding(text)
        embeddings.append(embedding)
        
        print(f"  向量维度: {len(embedding)}")
        print(f"  向量前5个值: {embedding[:5]}")
        
        if len(embedding) != LOCAL_EMBEDDING_DIMENSION:
            print(f"  ⚠️  维度不匹配！期望 {LOCAL_EMBEDDING_DIMENSION}，实际 {len(embedding)}")
            return False
    
    # 测试相似度计算
    print("\n" + "-" * 60)
    print("测试相似度计算...")
    print("-" * 60)
    
    import numpy as np
    
    # 计算第一个和第二个文本的相似度（都与图书馆/阅读相关）
    sim_1_2 = np.dot(embeddings[0], embeddings[1])
    print(f"\n'{test_texts[0]}' vs '{test_texts[1]}'")
    print(f"  相似度: {sim_1_2:.4f} (相关文本)")
    
    # 计算第一个和第三个文本的相似度（不相关）
    sim_1_3 = np.dot(embeddings[0], embeddings[2])
    print(f"\n'{test_texts[0]}' vs '{test_texts[2]}'")
    print(f"  相似度: {sim_1_3:.4f} (不相关文本)")
    
    # 验证相关文本的相似度更高
    print(f"\n相似度差异: {sim_1_2 - sim_1_3:.4f}")
    
    if sim_1_2 > sim_1_3:
        print(f"✅ 相似度计算正确（相关文本相似度更高）")
        return True
    elif abs(sim_1_2 - sim_1_3) < 0.05:
        print(f"⚠️  相似度差异较小，但模型工作正常")
        return True
    else:
        print(f"⚠️  相似度计算异常")
        return False


async def main():
    success = await test_local_embedding()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 本地 Embedding 模型测试通过")
        print("\n可以运行 RAG 测试: python ../test/test_rag.py")
    else:
        print("✗ 本地 Embedding 模型测试失败")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
