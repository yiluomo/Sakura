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
# 向量存储目录（FAISS索引文件）
# ─────────────────────────────────────────────────────────
_vector_store_env = os.environ.get("VECTOR_STORE_DIR")
if _vector_store_env:
    VECTOR_STORE_DIR = Path(_vector_store_env)
else:
    VECTOR_STORE_DIR = MEMORY_STORE_DIR / "vectors"  # 本地：Sakura/memory_store/vectors/
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

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

# 记忆导出/导入配置（用于备份和迁移）
MEMORY_EXPORT_DIR = SAKURA_ROOT / "memory_exports"  # 导出文件存储目录
MEMORY_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

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

# ─────────────────────────────────────────────────────────
# RAG 向量检索配置（FAISS）
# ─────────────────────────────────────────────────────────

# Embedding 模式选择：'local' 或 'api'
EMBEDDING_MODE = os.environ.get("EMBEDDING_MODE", "local")  # 默认使用本地模型

# 本地 Embedding 模型配置
# 可选模型：
# - "BAAI/bge-small-zh-v1.5": 高质量中文模型，512维，~95MB
# - "shibing624/text2vec-base-chinese": 轻量级中文，768维，~400MB
# - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 多语言，384维，~120MB
LOCAL_EMBEDDING_MODEL = os.environ.get("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
LOCAL_EMBEDDING_DIMENSION = int(os.environ.get("LOCAL_EMBEDDING_DIMENSION", "512"))

# API Embedding 模型配置（使用 OpenAI API 兼容接口）
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", LLM_API_KEY)  # 默认使用 LLM 的 key
EMBEDDING_API_BASE = os.environ.get("EMBEDDING_API_BASE", LLM_API_BASE)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")  # 或 deepseek-embedding
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1536"))  # text-embedding-3-small 的维度

# 根据模式选择实际使用的维度
ACTUAL_EMBEDDING_DIMENSION = LOCAL_EMBEDDING_DIMENSION if EMBEDDING_MODE == "local" else EMBEDDING_DIMENSION

# 向量检索配置
VECTOR_SEARCH_LIMIT = int(os.environ.get("VECTOR_SEARCH_LIMIT", "20"))  # 向量检索返回数量
VECTOR_SEARCH_SCORE_THRESHOLD = float(os.environ.get("VECTOR_SEARCH_SCORE_THRESHOLD", "0.5"))  # 相似度阈值

# 记忆召回配置
RECALL_SHORT_TERM_LIMIT = int(os.environ.get("RECALL_SHORT_TERM_LIMIT", "6"))  # 短期记忆条数
RECALL_VECTOR_LIMIT = int(os.environ.get("RECALL_VECTOR_LIMIT", "5"))  # 向量检索记忆条数
RECALL_LONG_TERM_LIMIT = int(os.environ.get("RECALL_LONG_TERM_LIMIT", "5"))  # 长期记忆条数

# ─────────────────────────────────────────────────────────
# 短期记忆自动归档配置
# SQLite conversations 表超过 SHORT_TERM_MAX 条时，
# 自动将最早的 SHORT_TERM_ARCHIVE_COUNT 条归档到长期记忆（不压缩，保留原文）
# ─────────────────────────────────────────────────────────
SHORT_TERM_MAX           = int(os.environ.get("SHORT_TERM_MAX",           "200"))  # 触发归档的对话条数上限
SHORT_TERM_ARCHIVE_COUNT = int(os.environ.get("SHORT_TERM_ARCHIVE_COUNT", "150"))  # 每次归档最早的 N 条

# ─────────────────────────────────────────────────────────
# API 访问令牌（静态 Token 认证）
# 前端应用将此 Token 硬编码在请求头 X-API-Token 中
# 可通过环境变量 API_TOKEN 覆盖（如需临时换 key 时使用）
# ─────────────────────────────────────────────────────────
API_TOKEN = os.environ.get("API_TOKEN", "sakura-private-token-a7f3k9z2m1p8q4w6")

# ─────────────────────────────────────────────────────────
# 图升文与画面识别模型配置（Vision Models）
# ─────────────────────────────────────────────────────────
IMAGE_TO_TEXT_MODEL = os.environ.get("IMAGE_TO_TEXT_MODEL", "minicpm-v")
IMAGE_TO_TEXT_API_KEY = os.environ.get("IMAGE_TO_TEXT_API_KEY", "sk-662cc6ddd16c46369fe799dea0855625")
IMAGE_TO_TEXT_API_BASE = os.environ.get("IMAGE_TO_TEXT_API_BASE", "https://api.deepseek.com/v1")

SCENE_RECOGNITION_MODEL = os.environ.get("SCENE_RECOGNITION_MODEL", "minicpm-v")
SCENE_RECOGNITION_API_KEY = os.environ.get("SCENE_RECOGNITION_API_KEY", "sk-662cc6ddd16c46369fe799dea0855625")
SCENE_RECOGNITION_API_BASE = os.environ.get("SCENE_RECOGNITION_API_BASE", "https://api.deepseek.com/v1")
# ─────────────────────────────────────────────────────────
# AI 厂商配置密钥与模块关联选择
# ─────────────────────────────────────────────────────────
PROVIDER_DEEPSEEK_KEY = os.environ.get("PROVIDER_DEEPSEEK_KEY", "sk-662cc6ddd16c46369fe799dea0855625")
PROVIDER_QWEN_KEY = os.environ.get("PROVIDER_QWEN_KEY", "")
PROVIDER_DOUBAO_KEY = os.environ.get("PROVIDER_DOUBAO_KEY", "")
PROVIDER_OPENAI_KEY = os.environ.get("PROVIDER_OPENAI_KEY", "")
PROVIDER_CUSTOM_BASE = os.environ.get("PROVIDER_CUSTOM_BASE", "")
PROVIDER_CUSTOM_KEY = os.environ.get("PROVIDER_CUSTOM_KEY", "")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek")
IMAGE_TO_TEXT_PROVIDER = os.environ.get("IMAGE_TO_TEXT_PROVIDER", "deepseek")
SCENE_RECOGNITION_PROVIDER = os.environ.get("SCENE_RECOGNITION_PROVIDER", "deepseek")
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "deepseek")


# ─────────────────────────────────────────────────────────
# 动态配置持久化与加载（支持后台动态修改配置并在运行时生效）
# ─────────────────────────────────────────────────────────
import json

SETTINGS_FILE = SAKURA_ROOT / "settings.json"

def load_dynamic_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 将数据覆盖到当前模块的全局变量中
                for key, val in data.items():
                    globals()[key] = val
                print(f"[INFO] 成功加载动态配置: {list(data.keys())}")
        except Exception as e:
            print(f"[WARNING] 载入动态配置失败: {e}")

# 执行载入
load_dynamic_settings()


def save_dynamic_settings(new_settings: dict) -> bool:
    """
    保存配置并在运行时即时更新当前全局状态
    """
    try:
        existing = {}
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
                
        existing.update(new_settings)
        
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
            
        # 同步更新当前模块 of 全局变量
        for key, val in existing.items():
            globals()[key] = val
            
        # 重新计算实际的 Embedding 维度以保证热更新正确生效
        globals()["ACTUAL_EMBEDDING_DIMENSION"] = (
            globals().get("LOCAL_EMBEDDING_DIMENSION", 512)
            if globals().get("EMBEDDING_MODE", "local") == "local"
            else globals().get("EMBEDDING_DIMENSION", 1536)
        )
            
        return True
    except Exception as e:
        print(f"[ERROR] 动态保存配置失败: {e}")
        return False

