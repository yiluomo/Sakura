from pathlib import Path
from urllib.parse import quote_plus

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 1. 先定义 db 文件夹路径（项目根目录下的 db 文件夹）
DB_DIR = PROJECT_ROOT / "db"
DB_DIR.mkdir(exist_ok=True)  # 确保 db 文件夹存在

# 2. 将 data 文件夹定义为 db 文件夹的子目录
DATA_DIR = DB_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # 确保 data 文件夹存在

# 数据库配置 - MySQL
# 格式: mysql+aiomysql://用户名:密码@主机:端口/数据库名

#我的电脑
# DATABASE_URL = "mysql+aiomysql://root:YaeSakura@localhost:3306/sakura_db"
#公司电脑
job_computer_psw = "asdag!331@dAaf"
encode_psw = quote_plus(job_computer_psw)
DATABASE_URL = (f"mysql+aiomysql://root:{encode_psw}@localhost:3306/sakura_db")

# LLM API 配置（用于对话总结）
LLM_API_KEY = "sk-662cc6ddd16c46369fe799dea0855625"  # 请替换为实际的API密钥
LLM_API_BASE = "https://api.deepseek.com/v1"  # 或其他兼容的API地址
LLM_MODEL = "deepseek-chat"  # 用于总结的模型

# 短期记忆压缩配置
MEMORY_COMPRESSION_THRESHOLD = 200  # 触发压缩的对话数量阈值
MEMORY_COMPRESSION_BATCH_SIZE = 150  # 每次压缩的对话数量
MEMORY_KEEP_RECENT_COUNT = 50  # 压缩后保留的最近对话数量