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