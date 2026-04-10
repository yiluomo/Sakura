# ─────────────────────────────────────────────
# Electron 前端 Dockerfile（多阶段构建）
# Stage 1: Node 构建 Electron 应用
# Stage 2: Nginx 托管静态资源（或按需打包 Electron 运行环境）
# ─────────────────────────────────────────────

# Stage 1: 构建 Electron 应用
FROM node:20-bullseye-slim AS builder

WORKDIR /app

# 安装构建必需的系统依赖（Debian）
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 build-essential libc6-dev libgtk-3-0 libnotify4 libnss3 \
    libxss1 libasound2 libx11-xcb1 libxcomposite1 libxdamage1 libxtst6 \
&& rm -rf /var/lib/apt/lists/*

# 复制依赖文件，优先利用缓存层
COPY package.json package-lock.json ./

# 配置国内镜像（加速 Electron 下载）
RUN npm config set registry https://registry.npmmirror.com/
ENV ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
ENV ELECTRON_CUSTOM_DIR="{{ version }}"

# 安装全部依赖（包含 devDependencies，构建阶段需要）
RUN npm install --no-optional --no-audit --registry=https://registry.npmmirror.com/

# 复制项目源码
COPY . .

# 构建：设置 Node 内存上限（避免构建内存溢出），执行 Electron 构建脚本
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=8192"
# 先执行前端打包，便于定位错误
RUN npm run build
# 再运行 electron-builder：单独一层可让错误日志更明显
RUN npx electron-builder

# Stage 2: Nginx 托管静态产物（若需纯 Web 部署，可调整为复制 dist 目录）
FROM nginx:1.25-alpine AS runner

# 删除默认 Nginx 配置，替换为自定义配置
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf

# 复制 Electron 构建输出的静态/运行产物（根据实际输出路径调整）
COPY --from=builder /app/dist /usr/share/nginx/html
# 若 Electron 构建输出在 release 目录，替换为：COPY --from=builder /app/release /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]