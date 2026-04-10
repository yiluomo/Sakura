FROM python:3.9-slim

WORKDIR /app

# 1. 安装系统依赖（编译 + 运行时依赖）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libgomp1 \
    sed \
    && rm -rf /var/lib/apt/lists/*

# 2. 升级 pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel packaging

# 3. 复制依赖并直接安装到系统环境
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt && \
    pip show packaging || pip install packaging

# 4. 复制源码
COPY src/ .

# 5. 创建日志目录
RUN mkdir -p /app/logs

# 6. 容器对外暴露的端口
EXPOSE 8000

# 7. 处理入口脚本（修复 Windows 换行符并授权）
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]