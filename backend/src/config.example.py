import os
from pathlib import Path
from urllib.parse import quote_plus

# src/ 目录
SRC_ROOT = Path(__file__).parent

# Sakura/ 根目录（src/ → backend/ → Sakura/）
SAKURA_ROOT = Path(__file__).parent.parent.parent

# 兼容旧引用
PROJECT_ROOT = SRC_ROOT

# db 相关目录
DB_DIR = SRC_ROOT / "db"
DB_DIR.mkdir(exist_ok=True)

DATA_DIR = DB_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────
# 长期记忆文件存储目录
# 优先读取环境变量 MEMORY_STORE_DIR（Docker 容器挂载时使用）
# 未设置则使用相对路径计算（本地开发）
# ─────────────────────────────────────────────────────────
_memory_store_env = os.environ.get("MEMORY_STORE_DIR")
if _memory_store_env:
    MEMORY_STORE_DIR = Path(_memory_store_env)
else:
    MEMORY_STORE_DIR = SAKURA_ROOT / "memory_store"   # 本地：Sakura/memory_store/
MEMORY_STORE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────
# 数据库配置
# 请根据你的 MySQL 设置修改以下配置
# ─────────────────────────────────────────────────────────
_db_url_env = os.environ.get("DATABASE_URL")
if _db_url_env:
    DATABASE_URL = _db_url_env                         # Docker 注入
else:
    # 【请修改为你的 MySQL 配置】
    # 示例配置（请根据实际情况修改）：
    # DATABASE_URL = "mysql+aiomysql://root:你的密码@localhost:3306/sakura_db"
    
    # 如果使用 XAMPP/WAMP，默认配置可能是：
    DATABASE_URL = "mysql+aiomysql://root:@localhost:3306/sakura_db"
    
    # 如果 MySQL 有密码：
    # _password = quote_plus("你的MySQL密码")
    # DATABASE_URL = f"mysql+aiomysql://root:{_password}@localhost:3306/sakura_db"

# ─────────────────────────────────────────────────────────
# LLM API 配置（用于对话和总结）
# 请替换为你的实际 API 密钥
# ─────────────────────────────────────────────────────────
LLM_API_KEY = "sk-your-deepseek-api-key-here"  # 请替换为实际的 DeepSeek API 密钥
LLM_API_BASE = "https://api.deepseek.com/v1"    # DeepSeek API 地址
LLM_MODEL = "deepseek-chat"                     # 模型名称

# ─────────────────────────────────────────────────────────
# Embedding 配置（用于向量检索）
# 可以使用与 LLM 相同的 API 密钥
# ─────────────────────────────────────────────────────────
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", LLM_API_KEY)  # 默认使用 LLM 的 key
EMBEDDING_API_BASE = os.environ.get("EMBEDDING_API_BASE", LLM_API_BASE)
EMBEDDING_MODEL = "text-embedding-3-small"      # 或 deepseek-embedding
EMBEDDING_DIMENSION = 1536                      # text-embedding-3-small 的维度

# ─────────────────────────────────────────────────────────
# 记忆导出/导入配置
# ─────────────────────────────────────────────────────────
MEMORY_EXPORT_DIR = SAKURA_ROOT / "memory_exports"  # 导出文件存储目录
MEMORY_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────
# TTS 语音合成配置
# ─────────────────────────────────────────────────────────

# 是否启用 TTS（False 时 /chat 接口 audio_url 始终返回 null）
TTS_ENABLED = os.environ.get("TTS_ENABLED", "true").lower() == "true"

# 当前使用的 TTS 引擎
# 支持：gpt_sovits
TTS_ENGINE = os.environ.get("TTS_ENGINE", "gpt_sovits")

# ─────────────────────────────────────────────────────────
# GPT-SoVITS 配置（本地部署引擎，无需联网）
# 如果没有 GPT-SoVITS 服务，可以设置 TTS_ENABLED = False
# ─────────────────────────────────────────────────────────

# API 服务地址（如果本地部署了 GPT-SoVITS）
GPT_SOVITS_BASE_URL = os.environ.get("GPT_SOVITS_BASE_URL", "http://127.0.0.1:9880")

# 参考音频（服务器端绝对路径）及对应台词与语言
# 如果没有 GPT-SoVITS，以下配置可以忽略
GPT_SOVITS_REF_AUDIO_PATH = os.environ.get(
    "GPT_SOVITS_REF_AUDIO_PATH",
    r"C:\path\to\reference.wav",  # 请替换为实际的参考音频路径
)
GPT_SOVITS_PROMPT_TEXT = os.environ.get("GPT_SOVITS_PROMPT_TEXT", "这个身体似乎不会老去，但我想见的人，却都离去了。")
GPT_SOVITS_PROMPT_LANG = os.environ.get("GPT_SOVITS_PROMPT_LANG", "zh")
GPT_SOVITS_TEXT_LANG = os.environ.get("GPT_SOVITS_TEXT_LANG", "zh")

# 合成参数（通常不需要修改）
GPT_SOVITS_SPEED_FACTOR = float(os.environ.get("GPT_SOVITS_SPEED_FACTOR", "1.0"))
GPT_SOVITS_MEDIA_TYPE = os.environ.get("GPT_SOVITS_MEDIA_TYPE", "wav")
GPT_SOVITS_TOP_K = int(os.environ.get("GPT_SOVITS_TOP_K", "15"))
GPT_SOVITS_TOP_P = float(os.environ.get("GPT_SOVITS_TOP_P", "1.0"))
GPT_SOVITS_TEMPERATURE = float(os.environ.get("GPT_SOVITS_TEMPERATURE", "1.0"))
GPT_SOVITS_SEED = int(os.environ.get("GPT_SOVITS_SEED", "-1"))
GPT_SOVITS_BATCH_SIZE = int(os.environ.get("GPT_SOVITS_BATCH_SIZE", "1"))
GPT_SOVITS_SAMPLE_STEPS = int(os.environ.get("GPT_SOVITS_SAMPLE_STEPS", "32"))
GPT_SOVITS_TIMEOUT = float(os.environ.get("GPT_SOVITS_TIMEOUT", "180"))

# 模型权重路径（留空则使用 GPT-SoVITS 服务默认加载的模型）
GPT_SOVITS_GPT_WEIGHTS = os.environ.get("GPT_SOVITS_GPT_WEIGHTS", "")
GPT_SOVITS_SOVITS_WEIGHTS = os.environ.get("GPT_SOVITS_SOVITS_WEIGHTS", "")

# 音频缓存目录
AUDIO_CACHE_DIR = SAKURA_ROOT / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缓存最大文件数
AUDIO_CACHE_MAX_FILES = int(os.environ.get("AUDIO_CACHE_MAX_FILES", "200"))

# ─────────────────────────────────────────────────────────
# RAG 向量检索配置
# ─────────────────────────────────────────────────────────

# Qdrant 向量数据库配置
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION_NAME", "conversations")

# 向量检索配置
VECTOR_SEARCH_LIMIT = int(os.environ.get("VECTOR_SEARCH_LIMIT", "20"))
VECTOR_SEARCH_SCORE_THRESHOLD = float(os.environ.get("VECTOR_SEARCH_SCORE_THRESHOLD", "0.5"))

# 记忆召回配置
RECALL_SHORT_TERM_LIMIT = int(os.environ.get("RECALL_SHORT_TERM_LIMIT", "6"))
RECALL_VECTOR_LIMIT = int(os.environ.get("RECALL_VECTOR_LIMIT", "5"))
RECALL_LONG_TERM_LIMIT = int(os.environ.get("RECALL_LONG_TERM_LIMIT", "5"))

# ─────────────────────────────────────────────────────────
# 配置说明
# ─────────────────────────────────────────────────────────
"""
配置完成后，请确保：
1. MySQL 服务正在运行
2. 已创建数据库 sakura_db
3. API 密钥有效且有额度
4. 如果使用 TTS，GPT-SoVITS 服务正在运行

测试数据库连接：
mysql -u root -p -e "USE sakura_db; SHOW TABLES;"

测试 API 连接：
curl -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'
"""
