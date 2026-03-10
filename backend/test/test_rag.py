"""
测试 RAG 向量检索功能
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.vector_store import (
    add_conversation_vector,
    search_similar_conversations,
    get_collection_stats,
    init_collection
)
from memory.recall import recall_context
from db.database import AsyncSessionLocal
from db.crud import save_conversation, get_recent_conversations


async def test_vector_generation():
    """测试向量生成功能"""
    print("=" * 60)
    print("测试 1: 向量生成")
    print("=" * 60)
    
    test_user = "test_rag_user"
    test_conversations = [
        ("user", "我今天去了图书馆看书", "calm", 4),
        ("sakura", "看书是很好的习惯呢，看了什么类型的书？", "warm", 3),
        ("user", "看了一本关于人工智能的书", "curious", 5),
        ("sakura", "人工智能...很有趣的领域。", "thoughtful", 3),
        ("user", "你对AI有什么看法吗？", "curious", 4),
        ("sakura", "我...也在思考这个问题。", "melancholy", 4),
    ]
    
    print(f"\n准备插入 {len(test_conversations)} 条测试对话...\n")
    
    vector_ids = []
    async with AsyncSessionLocal() as db:
        for role, content, emotion, importance in test_conversations:
            # 保存到数据库
            conv_id = await save_conversation(
                db, test_user, role, content,
                emotion_type=emotion,
                importance=importance
            )
            
            # 生成向量
            vector_id = await add_conversation_vector(
                user_id=test_user,
                conversation_id=conv_id,
                role=role,
                content=content,
                emotion_type=emotion,
                importance=importance
            )
            
            vector_ids.append(vector_id)
            status = "✓" if vector_id else "✗"
            print(f"{status} [{role:9s}] {content[:30]:30s} -> vector_id: {vector_id}")
    
    success_count = sum(1 for vid in vector_ids if vid)
    print(f"\n向量生成完成: {success_count}/{len(test_conversations)} 成功")
    
    return test_user, success_count > 0


async def test_vector_search(user_id: str):
    """测试向量检索功能"""
    print("\n" + "=" * 60)
    print("测试 2: 向量检索")
    print("=" * 60)
    
    test_queries = [
        "你喜欢读书吗？",
        "AI是什么？",
        "今天天气怎么样？",  # 不相关的查询
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        print("-" * 60)
        
        results = await search_similar_conversations(
            user_id=user_id,
            query_text=query,
            limit=3
        )
        
        if results:
            print(f"找到 {len(results)} 条相似对话:\n")
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                content = result.get('content', '')
                role = result.get('role', '')
                emotion = result.get('emotion_type', '')
                
                print(f"  {i}. [相似度: {score:.3f}] [{role}] {content[:50]}")
                print(f"     情绪: {emotion}")
        else:
            print("  未找到相似对话")


async def test_recall_context(user_id: str):
    """测试上下文回忆功能（整合测试）"""
    print("\n" + "=" * 60)
    print("测试 3: 上下文回忆（RAG整合）")
    print("=" * 60)
    
    test_message = "我们之前聊过关于AI的话题吗？"
    
    print(f"\n当前消息: '{test_message}'")
    print("-" * 60)
    
    context = await recall_context(user_id, current_message=test_message)
    
    print(f"\n回忆的上下文:\n")
    print(context)
    
    # 检查是否包含相关内容
    has_ai_content = "AI" in context or "人工智能" in context
    status = "✓" if has_ai_content else "✗"
    print(f"\n{status} 上下文中{'包含' if has_ai_content else '不包含'}AI相关内容")


async def test_vector_stats(user_id: str):
    """测试向量存储统计"""
    print("\n" + "=" * 60)
    print("测试 4: 向量存储统计")
    print("=" * 60)
    
    stats = get_collection_stats()
    
    print(f"\n向量存储统计:")
    print(f"  总向量数: {stats.get('vectors_count', 0)}")
    print(f"  元数据数: {stats.get('metadata_count', 0)}")
    print(f"  存储路径: {stats.get('storage_path', 'N/A')}")


async def test_database_consistency(user_id: str):
    """测试数据库与向量存储的一致性"""
    print("\n" + "=" * 60)
    print("测试 5: 数据库一致性检查")
    print("=" * 60)
    
    # 获取数据库中的对话数
    async with AsyncSessionLocal() as db:
        conversations = await get_recent_conversations(db, user_id, limit=1000)
        db_count = len(conversations)
    
    # 获取向量存储中的向量数
    stats = get_collection_stats()
    vector_count = stats.get('vectors_count', 0)
    
    print(f"\n数据库对话数: {db_count}")
    print(f"向量存储总数: {vector_count}")
    print(f"(注意: 向量存储包含所有用户的数据)")
    
    if db_count <= vector_count:
        print("✓ 数据合理（用户对话数 <= 总向量数）")
    else:
        print(f"⚠️  用户对话数多于总向量数，可能有向量未生成")


async def cleanup_test_data(user_id: str):
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("清理测试数据")
    print("=" * 60)
    
    response = input(f"\n是否删除用户 '{user_id}' 的测试数据？(y/n): ")
    
    if response.lower() == 'y':
        # 这里可以添加清理逻辑
        # 注意：需要同时清理数据库和向量存储
        print("⚠️  清理功能待实现（需要添加删除API）")
    else:
        print("保留测试数据")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("RAG 向量检索功能测试")
    print("=" * 60)
    
    # 初始化向量存储
    print("\n初始化向量存储...")
    if not init_collection():
        print("❌ 向量存储初始化失败")
        return
    
    try:
        # 测试1: 向量生成
        test_user, success = await test_vector_generation()
        
        if not success:
            print("\n❌ 向量生成失败，终止测试")
            return
        
        # 等待向量索引更新
        print("\n等待向量索引更新...")
        await asyncio.sleep(1)
        
        # 测试2: 向量检索
        await test_vector_search(test_user)
        
        # 测试3: 上下文回忆
        await test_recall_context(test_user)
        
        # 测试4: 向量统计
        await test_vector_stats(test_user)
        
        # 测试5: 一致性检查
        await test_database_consistency(test_user)
        
        # 清理测试数据
        await cleanup_test_data(test_user)
        
        print("\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
