from pathlib import Path

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
DATABASE_URL = "mysql+aiomysql://root:YaeSakura@localhost:3306/sakura_db"