from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    """对话历史表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_user_time', 'user_id', 'timestamp'),
    )

class LongTermMemory(Base):
    """长期记忆表"""
    __tablename__ = "long_term_memory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    memory_type = Column(String(50))  # 'profile', 'preference', 'event'
    key = Column(String(100))
    value = Column(Text)
    importance = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_user_type', 'user_id', 'memory_type'),
    )

class UserState(Base):
    """用户状态表"""
    __tablename__ = "user_states"
    
    user_id = Column(String(50), primary_key=True)
    affinity = Column(Integer, default=0)  # 亲密度
    mood = Column(String(20), default='calm')  # 情绪
    last_interaction = Column(DateTime, default=datetime.now)
    total_messages = Column(Integer, default=0)
