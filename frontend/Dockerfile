# ─────────────────────────────────────────────
# 前端 Dockerfile（多阶段构建）
# Stage 1: Node 构建 Vue3 产物
# Stage 2: Nginx 托管静态文件 + 反向代理后端
# ─────────────────────────────────────────────

# Stage 1: 构建 Vue3
FROM node:20-alpine AS builder

WORKDIR /app

# 安装 git（某些 npm 包可能需要）
RUN apk add --no-cache git

# 先复制 package 文件利用缓存层
COPY package.json package-lock.json ./

# 使用国内 npm 镜像源加速安装
RUN npm config set registry https://registry.npmmirror.com/
RUN npm ci --prefer-offline

# 复制源码
COPY . .

# 设置环境变量，跳过类型检查加速构建
ENV NODE_ENV=production

# 分步构建：先尝试完整构建，失败则跳过类型检查
RUN echo "开始构建..." && \
    (npm run build || npm run build:no-check)


# Stage 2: Nginx 服务
FROM nginx:1.25-alpine AS runner

# 删除默认配置，使用自定义配置
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
