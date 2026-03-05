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
# 支持：gpt_sovits
TTS_ENGINE = os.environ.get("TTS_ENGINE", "gpt_sovits")

# ─────────────────────────────────────────────────────────
# GPT-SoVITS 配置（本地部署引擎，无需联网）
# 启动服务：runtime\python.exe api_v2.py -a 127.0.0.1 -p 9880
# ─────────────────────────────────────────────────────────

# API 服务地址
GPT_SOVITS_BASE_URL     = os.environ.get("GPT_SOVITS_BASE_URL",     "http://127.0.0.1:9880")

# 参考音频（服务器端绝对路径）及对应台词与语言
GPT_SOVITS_REF_AUDIO_PATH = os.environ.get(
    "GPT_SOVITS_REF_AUDIO_PATH",
    r"e:/workspace/yiluomu/tts/v4/八重樱/reference_audios/中文/emotions/【默认】这个身体似乎不会老去，但我想见的人，却都离去了。.wav",
)
GPT_SOVITS_PROMPT_TEXT  = os.environ.get("GPT_SOVITS_PROMPT_TEXT",  "这个身体似乎不会老去，但我想见的人，却都离去了。")   # 参考音频对应台词
GPT_SOVITS_PROMPT_LANG  = os.environ.get("GPT_SOVITS_PROMPT_LANG",  "zh")  # 参考音频语言
GPT_SOVITS_TEXT_LANG    = os.environ.get("GPT_SOVITS_TEXT_LANG",    "zh")  # 合成文本语言

# 合成参数
GPT_SOVITS_SPEED_FACTOR  = float(os.environ.get("GPT_SOVITS_SPEED_FACTOR",  "1.0"))
GPT_SOVITS_MEDIA_TYPE    = os.environ.get("GPT_SOVITS_MEDIA_TYPE",    "wav")   # wav / ogg / aac / raw
GPT_SOVITS_TOP_K         = int(os.environ.get("GPT_SOVITS_TOP_K",     "15"))   # 采样 top-k
GPT_SOVITS_TOP_P         = float(os.environ.get("GPT_SOVITS_TOP_P",   "1.0"))  # 采样 top-p
GPT_SOVITS_TEMPERATURE   = float(os.environ.get("GPT_SOVITS_TEMPERATURE", "1.0"))  # 采样温度
GPT_SOVITS_SEED          = int(os.environ.get("GPT_SOVITS_SEED",      "-1"))   # -1=随机, 固定值=可复现
GPT_SOVITS_BATCH_SIZE    = int(os.environ.get("GPT_SOVITS_BATCH_SIZE", "1"))   # 批处理大小
GPT_SOVITS_SAMPLE_STEPS  = int(os.environ.get("GPT_SOVITS_SAMPLE_STEPS", "32"))  # V4 模型采样步数
# 单次合成超时（秒）：首次冷启动会下载 g2pw 模型约需 90s，设为 180s 保险
GPT_SOVITS_TIMEOUT       = float(os.environ.get("GPT_SOVITS_TIMEOUT", "180"))

# 模型权重路径（相对或绝对均可；留空则使用 GPT-SoVITS 服务默认加载的模型）
GPT_SOVITS_GPT_WEIGHTS    = os.environ.get("GPT_SOVITS_GPT_WEIGHTS",    "")
GPT_SOVITS_SOVITS_WEIGHTS = os.environ.get("GPT_SOVITS_SOVITS_WEIGHTS", "")

# 音频缓存目录（Sakura/audio_cache/，已加入 .gitignore）
AUDIO_CACHE_DIR = SAKURA_ROOT / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缓存最大文件数，超出时自动删除最旧的文件
AUDIO_CACHE_MAX_FILES = int(os.environ.get("AUDIO_CACHE_MAX_FILES", "200"))
