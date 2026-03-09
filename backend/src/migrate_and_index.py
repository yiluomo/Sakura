"""
migrate_and_index.py
数据库迁移 + 向量索引重建脚本（FAISS）

功能：
1. 为 conversations 表添加新字段（不删除数据）
2. 为所有旧对话生成向量索引（FAISS）

使用方法：
    python migrate_and_index.py
"""

import asyncio
from sqlalchemy import text
from db.database import AsyncSessionLocal
from db.crud import update_conversation_vector_id
from memory.vector_store import init_collection, add_conversation_vector


async def migrate_database():
    """步骤 1：迁移数据库结构"""
    print("\n" + "=" * 60)
    print("步骤 1：数据库结构迁移")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 迁移 conversations 表
            print("\n[1.1] 迁移 conversations 表...")
            result = await db.execute(text("DESCRIBE conversations"))
            columns = {row[0] for row in result.fetchall()}
            
            has_vector_id = "vector_id" in columns
            has_emotion_type = "emotion_type" in columns
            has_importance = "importance" in columns
            
            if not (has_vector_id and has_emotion_type and has_importance):
                print("添加新字段...")
                
                if not has_vector_id:
                    # vector_id: 存储 Qdrant 中的向量 ID，格式：user_id_conversation_id
                    # 用于关联 MySQL 对话记录和 Qdrant 向量数据
                    await db.execute(text(
                        "ALTER TABLE conversations ADD COLUMN vector_id VARCHAR(100) DEFAULT '' AFTER timestamp"
                    ))
                    print("  ✅ 添加 vector_id 字段（向量数据库关联 ID）")
                
                if not has_emotion_type:
                    # emotion_type: 保存对话时的情绪状态
                    # 可选值：calm（平静）、happy（愉悦）、melancholy（忧郁）、nostalgic（怀念）、guarded（警戒）
                    await db.execute(text(
                        "ALTER TABLE conversations ADD COLUMN emotion_type VARCHAR(20) DEFAULT 'calm' AFTER vector_id"
                    ))
                    print("  ✅ 添加 emotion_type 字段（情绪类型）")
                
                if not has_importance:
                    # importance: 对话重要度，1-5 级
                    # 用于检索时的权重计算，重要度高的对话优先召回
                    await db.execute(text(
                        "ALTER TABLE conversations ADD COLUMN importance INT DEFAULT 3 AFTER emotion_type"
                    ))
                    print("  ✅ 添加 importance 字段（重要度 1-5）")
                
                await db.commit()
            else:
                print("  ✅ conversations 表已是最新")
            
            # 2. 添加索引
            print("\n[1.2] 添加索引...")
            
            try:
                # idx_vector_id: 加速通过 vector_id 查询对话
                # 用于向量数据恢复、数据一致性检查
                await db.execute(text("CREATE INDEX idx_vector_id ON conversations(vector_id)"))
                print("  ✅ 添加 idx_vector_id 索引（加速向量关联查询）")
            except Exception as e:
                if "Duplicate key name" in str(e):
                    print("  ⏭️ idx_vector_id 索引已存在")
            
            try:
                # idx_importance: 加速按重要度排序查询
                # 用于检索时优先召回重要对话
                await db.execute(text("CREATE INDEX idx_importance ON conversations(importance)"))
                print("  ✅ 添加 idx_importance 索引（加速重要度查询）")
            except Exception as e:
                if "Duplicate key name" in str(e):
                    print("  ⏭️ idx_importance 索引已存在")
            
            await db.commit()
            
            # 3. 迁移 user_states 表（情绪系统）
            print("\n[1.3] 迁移 user_states 表（情绪系统）...")
            
            # 检查表是否存在
            try:
                await db.execute(text("DESCRIBE user_states"))
            except:
                # 表不存在，创建它
                await db.execute(text("""
                    CREATE TABLE user_states (
                        user_id VARCHAR(50) PRIMARY KEY,              -- 用户 ID
                        affinity INT DEFAULT 0,                       -- 亲密度（0-100）
                        mood INT DEFAULT 50,                          -- 心情值（0-100，50 为中性）
                        emotion_type VARCHAR(20) DEFAULT 'calm',      -- 情绪类型（calm/happy/melancholy/nostalgic/guarded）
                        energy_level INT DEFAULT 80,                  -- 精力值（0-100）
                        emotion_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 情绪更新时间
                        last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,    -- 最后交互时间
                        total_messages INT DEFAULT 0                  -- 总消息数
                    )
                """))
                print("  ✅ 创建 user_states 表")
                await db.commit()
            
            # 添加情绪系统字段（如果不存在）
            alter_statements = [
                ("ALTER TABLE user_states MODIFY COLUMN mood INT DEFAULT 50", 
                 "mood 改为 INT 类型（心情值 0-100）"),
                ("ALTER TABLE user_states ADD COLUMN emotion_type VARCHAR(20) DEFAULT 'calm'", 
                 "emotion_type（情绪类型：calm/happy/melancholy/nostalgic/guarded）"),
                ("ALTER TABLE user_states ADD COLUMN energy_level INT DEFAULT 80", 
                 "energy_level（精力值 0-100）"),
                ("ALTER TABLE user_states ADD COLUMN emotion_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP", 
                 "emotion_updated_at（情绪更新时间）"),
            ]
            
            for sql, desc in alter_statements:
                try:
                    await db.execute(text(sql))
                    print(f"  ✅ 添加/修改 {desc}")
                except Exception as e:
                    if "Duplicate column" in str(e) or "check that it exists" in str(e):
                        print(f"  ⏭️ {desc} 已存在")
                    else:
                        print(f"  ⚠️ {desc}: {e}")
            
            await db.commit()
            
            print("\n✅ 数据库结构迁移完成")
            return True
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            return False


async def rebuild_vectors():
    """步骤 2：为所有对话重建向量索引（FAISS）"""
    print("\n" + "=" * 60)
    print("步骤 2：重建向量索引（FAISS）")
    print("=" * 60)
    
    # 初始化 FAISS
    print("\n初始化 FAISS 向量存储...")
    if not init_collection():
        print("❌ FAISS 初始化失败")
        return False
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取所有对话 ID
            print("\n统计对话数量...")
            result = await db.execute(text("SELECT COUNT(*) FROM conversations"))
            total_count = result.scalar()
            print(f"📊 共有 {total_count} 条对话需要建立索引")
            
            if total_count == 0:
                print("✅ 没有对话需要处理")
                return True
            
            # 分批处理
            batch_size = 100
            processed = 0
            failed = 0
            
            print(f"\n开始处理（每批 {batch_size} 条）...")
            
            for offset in range(0, total_count, batch_size):
                # 获取一批对话
                result = await db.execute(text(
                    f"SELECT id, user_id, role, content, emotion_type, importance, timestamp "
                    f"FROM conversations ORDER BY id LIMIT {batch_size} OFFSET {offset}"
                ))
                conversations = result.fetchall()
                
                # 为每条对话生成向量
                for conv in conversations:
                    conv_id, user_id, role, content, emotion_type, importance, timestamp = conv
                    
                    try:
                        # 生成向量
                        vector_id = await add_conversation_vector(
                            user_id=user_id,
                            conversation_id=conv_id,
                            role=role,
                            content=content,
                            emotion_type=emotion_type or "calm",
                            importance=importance or 3,
                            timestamp=timestamp
                        )
                        
                        # 更新数据库中的 vector_id
                        if vector_id:
                            await update_conversation_vector_id(db, conv_id, vector_id)
                            processed += 1
                        else:
                            failed += 1
                            print(f"  ⚠️ 对话 {conv_id} 向量生成失败")
                        
                    except Exception as e:
                        failed += 1
                        print(f"  ❌ 对话 {conv_id} 处理失败: {e}")
                
                # 显示进度
                progress = min(offset + batch_size, total_count)
                print(f"  进度: {progress}/{total_count} ({progress*100//total_count}%)")
            
            print(f"\n✅ 向量索引重建完成")
            print(f"   成功: {processed} 条")
            print(f"   失败: {failed} 条")
            
            return failed == 0
            
        except Exception as e:
            print(f"\n❌ 向量重建失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("数据库迁移 + 向量索引重建（FAISS）")
    print("=" * 60)
    print("\n⚠️  请确保：")
    print("1. MySQL 数据库已启动")
    print("2. 已配置 config.py 中的 API Key")
    print("\n按 Enter 继续，Ctrl+C 取消...")
    input()
    
    # 步骤 1：迁移数据库
    if not await migrate_database():
        print("\n❌ 数据库迁移失败，终止操作")
        return
    
    # 步骤 2：重建向量
    if not await rebuild_vectors():
        print("\n⚠️ 向量重建部分失败，但数据库迁移已完成")
        print("   可以稍后重新运行此脚本继续重建向量")
        return
    
    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print("=" * 60)
    print("\n现在可以启动应用：")
    print("  python main.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
