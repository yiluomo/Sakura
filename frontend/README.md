# Sakura UI AI Chat

一个基于 Vue 3 + TypeScript 的现代化 AI 对话前端应用，提供类似 ChatGPT 的对话体验，支持长期记忆功能和深色主题。

## ✨ 特性

- 🚀 **现代化技术栈**: Vue 3 + TypeScript + Vite + Pinia
- 💬 **ChatGPT 风格界面**: 类似 ChatGPT 的对话体验，支持流式响应
- 🧠 **长期记忆功能**: 基于关键词的智能记忆保存和管理
- 🎨 **深色主题**: 支持深色/浅色主题切换
- 📱 **响应式设计**: 完美适配桌面端和移动端
- ⚡ **高性能**: 优化的组件和状态管理，流畅的用户体验
- 🛡️ **类型安全**: 完整的 TypeScript 支持

## 🛠️ 技术栈

- **框架**: Vue 3.x (Composition API)
- **构建工具**: Vite 5.x
- **状态管理**: Pinia
- **UI 组件库**: Element Plus
- **HTTP 客户端**: Axios
- **类型检查**: TypeScript
- **样式预处理**: SCSS
- **代码规范**: ESLint + Prettier

## 📁 项目结构

```
src/
├── api/             # API 请求模块
│   ├── index.ts     # API 客户端配置
│   ├── chat.ts      # 聊天相关 API
│   └── memory.ts    # 记忆相关 API
├── assets/          # 静态资源
├── components/      # 公共组件
│   ├── chat/        # 对话相关组件
│   │   ├── ChatMessage.vue
│   │   └── ChatInput.vue
│   ├── memory/      # 记忆相关组件
│   │   ├── MemoryConfirmation.vue
│   │   └── MemoryDialog.vue
│   └── ui/          # UI 基础组件
├── composables/     # 组合式函数
├── directives/      # 自定义指令
├── layouts/         # 布局组件
├── plugins/         # 插件
├── router/          # 路由配置
│   └── index.ts
├── stores/          # Pinia 状态管理
│   ├── chat.ts      # 聊天状态
│   ├── memory.ts    # 记忆状态
│   └── ui.ts        # UI 状态
├── styles/          # 全局样式
│   └── main.scss
├── types/           # TypeScript 类型定义
│   └── index.ts
├── utils/           # 工具函数
├── views/           # 页面组件
│   ├── ChatView.vue # 聊天页面
│   └── MemoryView.vue # 记忆管理页面
├── App.vue          # 根组件
└── main.ts          # 应用入口
```

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 7.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 开发环境

```bash
# 启动开发服务器
npm run dev

# 或使用 yarn
yarn dev
```

应用将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
# 构建生产版本
npm run build

# 或使用 yarn
yarn build
```

### 预览生产版本

```bash
# 预览构建结果
npm run preview

# 或使用 yarn
yarn preview
```

## 🔧 配置

### 环境变量

创建 `.env` 文件在项目根目录：

```env
# API 基础 URL
VITE_API_BASE_URL=http://localhost:8080/api

# 其他环境变量
VITE_APP_TITLE=Sakura UI AI Chat
```

### API 配置

修改 `src/api/index.ts` 中的 API 配置：

```typescript
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})
```

## 📖 API 文档

### 聊天 API

#### 发送消息

```typescript
POST /api/chat
Content-Type: application/json

{
  "message": "你好",
  "conversationId": "optional-conversation-id",
  "stream": true
}
```

#### 流式响应

```typescript
POST /api/chat/stream
Content-Type: application/json

{
  "message": "你好",
  "conversationId": "optional-conversation-id"
}
```

### 记忆 API

#### 获取记忆列表

```typescript
GET /api/memory
```

#### 创建记忆

```typescript
POST /api/memory
Content-Type: application/json

{
  "content": "记忆内容",
  "category": "分类",
  "keywords": ["关键词1", "关键词2"]
}
```

#### 更新记忆

```typescript
PUT /api/memory/:id
Content-Type: application/json

{
  "content": "更新的内容",
  "category": "更新的分类",
  "keywords": ["更新的关键词"]
}
```

#### 删除记忆

```typescript
DELETE /api/memory/:id
```

## 🎨 组件使用

### ChatMessage 组件

```vue
<ChatMessage
  :message="message"
  @retry="handleRetry"
  @delete="handleDelete"
/>
```

### ChatInput 组件

```vue
<ChatInput
  :is-loading="isLoading"
  @send="handleSendMessage"
/>
```

### MemoryConfirmation 组件

```vue
<MemoryConfirmation
  v-model="showDialog"
  :content="content"
  :keywords="keywords"
  @confirm="handleMemoryConfirm"
/>
```

## 🧠 记忆功能

应用支持基于关键词的长期记忆功能：

1. **关键词检测**: 自动检测对话中的预设关键词
2. **二次确认**: 弹出确认对话框，让用户确认保存内容
3. **记忆管理**: 提供记忆的查看、编辑、删除功能
4. **分类标签**: 支持自定义分类和关键词标签

### 预设关键词

默认关键词包括：`重要`、`记住`、`备忘`、`提醒`、`关键`、`核心`、`要点`

## 🎯 主题定制

### CSS 变量

应用使用 CSS 变量进行主题定制，可在 `src/styles/main.scss` 中修改：

```scss
:root {
  --el-color-primary: #409eff;
  --el-bg-color: #ffffff;
  --el-text-color-primary: #303133;
  // ... 更多变量
}
```

### 深色主题

深色主题会自动应用 `.dark-theme` 类，相关样式已预定义。

## 🔍 代码规范

项目使用 ESLint + Prettier 进行代码规范检查：

```bash
# 检查代码规范
npm run lint

# 自动修复代码格式
npm run format
```

## 📱 响应式设计

应用支持响应式设计，在不同设备上都有良好的体验：

- **桌面端**: 完整功能界面
- **平板端**: 适配触摸操作
- **手机端**: 优化的移动端界面

## 🚀 部署

### Docker 部署

```dockerfile
FROM node:16-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Vercel 部署

1. 将代码推送到 GitHub
2. 在 Vercel 中导入项目
3. 配置环境变量
4. 部署完成

