"""
测试迁移脚本的 SQL 语法
验证保留关键字是否正确处理
"""

import asyncio
from sqlalchemy import text
from db.database import AsyncSessionLocal
from config import DB_IS_SQLITE


async def test_long_term_memory_query():
    """测试长期记忆查询 SQL 语法"""
    print("测试长期记忆查询 SQL...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 测试 COUNT 查询
            result = await db.execute(text("SELECT COUNT(*) FROM long_term_memory"))
            count = result.scalar()
            print(f"✅ COUNT 查询成功: {count} 条记录")
            
            # 测试带保留关键字的 SELECT 查询
            result = await db.execute(text(
                "SELECT id, memory_type, `key`, `value`, importance "
                "FROM long_term_memory ORDER BY id LIMIT 5"
            ))
            memories = result.fetchall()
            print(f"✅ SELECT 查询成功: 获取 {len(memories)} 条记录")
            
            # 显示前几条记录
            for mem in memories[:3]:
                mem_id, memory_type, key, value, importance = mem
                print(f"  - ID={mem_id}, type={memory_type}, key={key[:20] if key else 'None'}...")
            
            return True
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_vector_id_field():
    """测试 vector_id 字段是否存在"""
    print("\n测试 vector_id 字段...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查字段是否存在
            if DB_IS_SQLITE:
                result = await db.execute(text("PRAGMA table_info(long_term_memory)"))
                columns = {row[1] for row in result.fetchall()}
            else:
                result = await db.execute(text("DESCRIBE long_term_memory"))
                columns = {row[0] for row in result.fetchall()}
            
            if "vector_id" in columns:
                print("✅ vector_id 字段已存在")
                
                # 测试查询 vector_id
                result = await db.execute(text(
                    "SELECT id, vector_id FROM long_term_memory LIMIT 5"
                ))
                records = result.fetchall()
                
                filled_count = sum(1 for r in records if r[1])
                print(f"   前 5 条记录中有 {filled_count} 条已填充 vector_id")
                
                return True
            else:
                print("⚠️ vector_id 字段不存在，需要运行迁移脚本")
                return False
                
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("迁移脚本 SQL 语法测试")
    print("=" * 60)
    
    # 测试 1: 查询语法
    success1 = await test_long_term_memory_query()
    
    # 测试 2: vector_id 字段
    success2 = await test_vector_id_field()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ 所有测试通过")
    else:
        print("⚠️ 部分测试失败")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
