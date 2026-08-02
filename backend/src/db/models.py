from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    """对话历史表（支持向量检索）"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'sakura'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    # 向量检索相关字段
    vector_id = Column(String(100), default="")  # Qdrant 中的向量 ID
    emotion_type = Column(String(20), default="calm")  # 保存时的情绪状态
    importance = Column(Integer, default=3)  # 重要度 1-5
    
    __table_args__ = (
        Index('idx_user_time', 'user_id', 'timestamp'),
        Index('idx_vector_id', 'vector_id'),
        Index('idx_importance', 'importance'),
    )

class LongTermMemory(Base):
    """长期记忆索引表（与 memory_store/*.md 文件双轨并行）"""
    __tablename__ = "long_term_memory"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    memory_type = Column(String(50),  nullable=False)           # 记忆类型：name/hobby/manual/conversation_summary 等
    key         = Column(String(100), nullable=False)           # 条目唯一标识键，如 "我叫"、"我喜欢"
    value       = Column(Text)                                  # 内容摘要（前100字），便于快速预览
    keywords    = Column(String(500), default="")               # LLM 提取的关键词，逗号分隔
    file_path   = Column(String(200), default="")               # 对应 .md 文件的相对路径，如 "memory_store/profile.md"
    importance  = Column(Integer, default=1)                    # 重要度 1~5
    emotion_tag = Column(String(20), default="")                # 保存时的情绪状态（预留给情绪系统）
    emotional_intensity = Column(Integer, default=0)            # 情感强度 0~5（预留给情绪系统）
    created_at  = Column(DateTime, default=datetime.now)
    updated_at  = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    vector_id   = Column(String(100), default="")               # 向量数据库关联 ID

    __table_args__ = (
        Index('idx_type_key',    'memory_type', 'key'),         # 去重 / 精确查找
        Index('idx_ltm_importance', 'importance'),               # 按重要度排序
        Index('idx_ltm_vector_id',  'vector_id'),                # 向量关联查询
    )

class UserState(Base):
    """用户状态表"""
    __tablename__ = "user_states"
    
    user_id = Column(String(50), primary_key=True)
    affinity = Column(Integer, default=0)  # 亲密度
    mood = Column(Integer, default=50)  # 情绪值 0-100，50为中性
    emotion_type = Column(String(20), default='calm')  # 情绪类型：calm/happy/melancholy/nostalgic/guarded
    energy_level = Column(Integer, default=80)  # 精力值 0-100
    emotion_updated_at = Column(DateTime, default=datetime.now)  # 情绪更新时间
    last_interaction = Column(DateTime, default=datetime.now)
    total_messages = Column(Integer, default=0)
