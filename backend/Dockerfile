# ─────────────────────────────────────────────
# 后端 Dockerfile
# 多阶段构建：builder 安装依赖，runner 运行服务
# ─────────────────────────────────────────────

# Stage 1: 安装依赖
FROM python:3.9-slim AS builder

WORKDIR /install

# 安装系统依赖（编译某些 Python 包需要）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip 和安装构建工具
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 只复制依赖声明（利用 Docker 层缓存）
COPY requirements.txt .

# 使用国内 PyPI 镜像源加速安装
RUN pip install --no-cache-dir --prefix=/install/deps \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    -r requirements.txt


# Stage 2: 运行镜像
FROM python:3.9-slim AS runner

WORKDIR /app

# 从 builder 复制已安装的依赖
COPY --from=builder /install/deps /usr/local

# 复制源码
COPY src/ .

# 创建日志目录
RUN mkdir -p /app/logs

# 容器对外暴露的端口
EXPOSE 8000

# 使用 entrypoint 脚本：先迁移数据库，再启动服务
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
