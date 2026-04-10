#!/bin/sh
# entrypoint.sh —— 后端容器启动脚本
# 1. 等待 MySQL 就绪
# 2. 执行数据库迁移（建表 / 更新结构）
# 3. 启动 FastAPI 服务

set -e

echo "======================================"
echo " 🌸 Sakura Backend 启动"
echo "======================================"

# ── 等待 MySQL 就绪 ──────────────────────
echo "[1/3] 等待 MySQL 就绪..."
MAX_TRIES=30
COUNT=0
until python -c "
import asyncio, aiomysql, os, sys
from urllib.parse import urlparse

url = os.environ.get('DATABASE_URL', '')
try:
    url = url.replace('mysql+aiomysql://', '')
    cred, rest = url.split('@')
    user, psw = cred.split(':', 1)
    host_port, db = rest.split('/', 1)
    host = host_port.split(':')[0]
    port = int(host_port.split(':')[1]) if ':' in host_port else 3306

    async def check():
        conn1 = await aiomysql.connect(host=host, port=port, user=user, password=psw)
        async with conn1.cursor() as cur:
            await cur.execute(f\"CREATE DATABASE IF NOT EXISTS \`{db}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci\")
        conn1.close()
        conn2 = await aiomysql.connect(host=host, port=port, user=user, password=psw, db=db)
        conn2.close()

    asyncio.run(check())
    print('MySQL 已就绪')
except Exception as e:
    print(f'等待中: {e}')
    sys.exit(1)
" 2>/dev/null; do
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_TRIES ]; then
        echo "❌ MySQL 等待超时，请检查数据库连接配置"
        exit 1
    fi
    echo "   MySQL 未就绪，${COUNT}/${MAX_TRIES}，3秒后重试..."
    sleep 3
done

# ── 执行数据库初始化与同步 ────────────────────────
echo "[2/3] 执行数据库初始化与同步..."
python setup_db.py
echo "   ✅ 数据库设置完成"

# ── 启动 FastAPI 服务 ─────────────────────
echo "[3/3] 启动 Uvicorn 服务..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
