"""
init_db.py
数据库初始化脚本（全新安装使用）

功能：
1. 创建所有数据库表
2. 初始化默认数据
3. 验证表结构

使用方法：
    python init_db.py
"""

import asyncio
from sqlalchemy import text
from db.database import engine, AsyncSessionLocal
from db.models import Base, UserState, Conversation, LongTermMemory


async def init_database():
    """初始化数据库"""
    print("\n" + "=" * 60)
    print("数据库初始化")
    print("=" * 60)
    
    try:
        # 1. 创建所有表
        print("\n[1/3] 创建数据库表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✅ conversations 表")
        print("  ✅ long_term_memory 表")
        print("  ✅ user_states 表")
        
        # 2. 初始化默认用户状态
        print("\n[2/3] 初始化默认数据...")
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(text("""
                    INSERT INTO user_states (
                        user_id,                -- 用户 ID
                        affinity,               -- 亲密度（0-100）
                        mood,                   -- 心情值（0-100，50 为中性）
                        emotion_type,           -- 情绪类型（calm/happy/melancholy/nostalgic/guarded）
                        energy_level,           -- 精力值（0-100）
                        emotion_updated_at,     -- 情绪更新时间
                        last_interaction,       -- 最后交互时间
                        total_messages          -- 总消息数
                    )
                    VALUES ('default_user', 0, 50, 'calm', 80, NOW(), NOW(), 0)
                    ON DUPLICATE KEY UPDATE user_id=user_id
                """))
                await db.commit()
                print("  ✅ 默认用户状态已创建")
            except Exception as e:
                print(f"  ⚠️ 初始化用户状态: {e}")
        
        # 3. 验证表结构
        print("\n[3/3] 验证表结构...")
        async with AsyncSessionLocal() as db:
            # 验证 conversations 表
            result = await db.execute(text("DESCRIBE conversations"))
            conv_columns = [row[0] for row in result.fetchall()]
            required_conv = [
                "id",            # 主键
                "user_id",       # 用户 ID
                "role",          # 角色（user/sakura）
                "content",       # 对话内容
                "timestamp",     # 时间戳
                "vector_id",     # Qdrant 向量 ID
                "emotion_type",  # 情绪类型
                "importance"     # 重要度（1-5）
            ]
            
            if all(col in conv_columns for col in required_conv):
                print("  ✅ conversations 表结构正确")
            else:
                missing = [col for col in required_conv if col not in conv_columns]
                print(f"  ❌ conversations 表缺少字段: {missing}")
                return False
            
            # 验证 long_term_memory 表
            result = await db.execute(text("DESCRIBE long_term_memory"))
            ltm_columns = [row[0] for row in result.fetchall()]
            required_ltm = [
                "id",            # 主键
                "memory_type",   # 记忆类型（name/hobby/manual 等）
                "key",           # 触发关键词
                "value",         # 内容摘要（前 100 字）
                "keywords",      # LLM 提取的关键词
                "file_path",     # 对应的 .md 文件路径
                "importance"     # 重要度（1-5）
            ]
            
            if all(col in ltm_columns for col in required_ltm):
                print("  ✅ long_term_memory 表结构正确")
            else:
                missing = [col for col in required_ltm if col not in ltm_columns]
                print(f"  ❌ long_term_memory 表缺少字段: {missing}")
                return False
            
            # 验证 user_states 表
            result = await db.execute(text("DESCRIBE user_states"))
            us_columns = [row[0] for row in result.fetchall()]
            required_us = [
                "user_id",            # 用户 ID（主键）
                "affinity",           # 亲密度（0-100）
                "mood",               # 心情值（0-100）
                "emotion_type",       # 情绪类型
                "energy_level",       # 精力值（0-100）
                "last_interaction"    # 最后交互时间
            ]
            
            if all(col in us_columns for col in required_us):
                print("  ✅ user_states 表结构正确")
            else:
                missing = [col for col in required_us if col not in us_columns]
                print(f"  ❌ user_states 表缺少字段: {missing}")
                return False
        
        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        print("\n下一步：")
        print("1. 启动 Qdrant：.\\start_qdrant.ps1")
        print("2. 启动应用：python main.py")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Sakura 数据库初始化")
    print("=" * 60)
    print("\n⚠️  请确保：")
    print("1. MySQL 数据库已启动")
    print("2. 已创建数据库：CREATE DATABASE sakura_db;")
    print("3. 已配置 config.py 中的 DATABASE_URL")
    print("\n按 Enter 继续，Ctrl+C 取消...")
    input()
    
    success = await init_database()
    
    if not success:
        print("\n❌ 初始化失败，请检查错误信息")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
