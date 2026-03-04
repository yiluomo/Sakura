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
# 优先读取环境变量 DATABASE_URL（Docker / CI 时注入）
# 未设置则使用本地硬编码配置
# ─────────────────────────────────────────────────────────
_db_url_env = os.environ.get("DATABASE_URL")
if _db_url_env:
    DATABASE_URL = _db_url_env                         # Docker 注入
else:
    #【个人电脑】
    # DATABASE_URL = "mysql+aiomysql://root:YaeSakura@localhost:3306/sakura_db"

    #【公司电脑】（当前激活）
    _psw = quote_plus("asdag!331@dAaf")
    DATABASE_URL = f"mysql+aiomysql://root:{_psw}@localhost:3306/sakura_db"

# LLM API 配置（用于对话总结）
LLM_API_KEY = "sk-662cc6ddd16c46369fe799dea0855625"  # 请替换为实际的API密钥
LLM_API_BASE = "https://api.deepseek.com/v1"  # 或其他兼容的API地址
LLM_MODEL = "deepseek-chat"  # 用于总结的模型

# 短期记忆压缩配置
MEMORY_COMPRESSION_THRESHOLD = 200  # 触发压缩的对话数量阈值
MEMORY_COMPRESSION_BATCH_SIZE = 150  # 每次压缩的对话数量
MEMORY_KEEP_RECENT_COUNT = 50  # 压缩后保留的最近对话数量

# ─────────────────────────────────────────────────────────
# TTS 语音合成配置
# ─────────────────────────────────────────────────────────

# 是否启用 TTS（False 时 /chat 接口 audio_url 始终返回 null）
TTS_ENABLED = os.environ.get("TTS_ENABLED", "true").lower() == "true"

# 当前使用的 TTS 引擎（修改此处即可切换引擎）
# 支持：fish_audio
TTS_ENGINE = os.environ.get("TTS_ENGINE", "fish_audio")

# Fish Audio 配置
FISH_AUDIO_API_KEY  = os.environ.get("FISH_AUDIO_API_KEY",  "29f45a8c3744438faf291b84d4537b52")
FISH_AUDIO_MODEL_ID = os.environ.get("FISH_AUDIO_MODEL_ID", "507248329802416cb183d0b74be182bf")

# 音频缓存目录（Sakura/audio_cache/，已加入 .gitignore）
AUDIO_CACHE_DIR = SAKURA_ROOT / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缓存最大文件数，超出时自动删除最旧的文件
AUDIO_CACHE_MAX_FILES = int(os.environ.get("AUDIO_CACHE_MAX_FILES", "200"))
