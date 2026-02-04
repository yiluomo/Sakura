# 项目模块结构

## 根目录

```
樱/
├── backend/          # 后端服务
├── frontend/         # 前端界面
├── docs/            # 项目文档
├── Agent_models/    # AI模型配置
├── .git/            # Git 版本控制
├── .idea/           # IDE 配置
├── .gitignore       # Git 忽略规则
└── README.md        # 项目说明
```

## Backend 模块

```
backend/
├── src/             # 源代码
├── test/            # 测试脚本
└── environment.yml  # Conda 环境配置
```

### src/ - 源代码

```
src/
├── api/             # API 层 - 世界入口
├── core/            # Core 层 - 意识中枢
├── llm/             # LLM 层 - 大脑适配器
├── memory/          # Memory 层 - 记忆系统
├── db/              # DB 层 - 持久化
├── models/          # 数据模型
├── config.py        # 配置文件
└── main.py          # 应用入口
```

#### api/ - API 层

| 文件 | 职责 |
|------|------|
| `chat.py` | 对话接口 |
| `__init__.py` | 模块初始化 |

#### core/ - Core 层

| 文件 | 职责 |
|------|------|
| `conversation.py` | 对话调度器 |
| `person.py` | 人格系统 |
| `prompt.py` | 提示词构建 |
| `state.py` | 状态系统 |
| `__init__.py` | 模块初始化 |

#### llm/ - LLM 层

| 文件 | 职责 |
|------|------|
| `adapter.py` | 统一接口 |
| `llmModel/ollama.py` | Ollama 实现 |
| `llmModel/dpsk.py` | DeepSeek API 实现 |
| `__init__.py` | 模块初始化 |

#### memory/ - Memory 层

| 文件 | 职责 |
|------|------|
| `short_term.py` | 短期记忆 |
| `long_term.py` | 长期记忆 |
| `recall.py` | 回忆机制 |
| `__init__.py` | 模块初始化 |

#### db/ - DB 层

| 文件 | 职责 |
|------|------|
| `database.py` | 数据库引擎和会话管理 |
| `models.py` | SQLAlchemy 数据模型 |
| `crud.py` | 数据库 CRUD 操作 |
| `__init__.py` | 模块初始化 |

**数据库**: MySQL (sakura_db)

**数据表**:
- `conversations`: 对话历史（包含timestamp）
- `long_term_memory`: 长期记忆
- `user_states`: 用户状态（亲密度、情绪）

#### models/ - 数据模型

| 文件 | 职责 |
|------|------|
| `schemas.py` | 数据结构定义 |
| `__init__.py` | 模块初始化 |

### test/ - 测试

| 文件 | 职责 |
|------|------|
| `test_chat.py` | 对话测试脚本（交互式）|

## Frontend 模块

```
frontend/
├── src/             # 源代码
│   ├── api/         # API 接口
│   ├── asserts/     # 静态资源（图片等）
│   ├── components/  # Vue 组件
│   ├── router/      # 路由配置
│   ├── stores/      # Pinia 状态管理
│   ├── styles/      # 样式文件
│   ├── types/       # TypeScript 类型定义
│   ├── views/       # 页面视图
│   ├── App.vue      # 根组件
│   └── main.ts      # 入口文件
├── node_modules/    # 依赖包
├── package.json     # 项目配置
├── vite.config.ts   # Vite 配置
└── tsconfig.json    # TypeScript 配置
```

**技术栈**:
- Vue 3 + TypeScript
- Element Plus UI 组件库
- Pinia 状态管理
- Vite 构建工具

## Docs 模块

```
docs/
├── logs/            # 日志文件
├── sakura/          # 项目文档
│   ├── 开发文档.md
│   ├── project.md   # 本文件
│   └── sakura.md
└── write/           # 写作文档
```

## 数据流

```
用户请求
  ↓
api/chat.py (接收请求)
  ↓
core/conversation.py (对话调度)
  ↓
├─ memory/recall.py      (从数据库回忆上下文)
├─ core/person.py        (加载人格)
├─ core/prompt.py        (构建提示词)
├─ llm/adapter.py        (调用 DeepSeek/Ollama)
├─ memory/short_term.py  (保存到数据库)
└─ memory/long_term.py   (提取并保存长期记忆)
  ↓
返回回复
```

## 数据库结构

```
MySQL: sakura_db
├─ conversations        (对话历史)
│  ├─ id
│  ├─ user_id
│  ├─ role (user/assistant)
│  ├─ content
│  └─ timestamp
├─ long_term_memory     (长期记忆)
│  ├─ id
│  ├─ user_id
│  ├─ memory_type (profile/preference/event)
│  ├─ key
│  ├─ value
│  ├─ importance
│  └─ created_at/updated_at
└─ user_states          (用户状态)
   ├─ user_id (主键)
   ├─ affinity (亲密度)
   ├─ mood (情绪)
   ├─ last_interaction
   └─ total_messages
```

## 技术栈

**后端**:
- **框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy (异步)
- **大模型**: DeepSeek API / Ollama
- **HTTP 客户端**: httpx (异步)
- **环境**: Python 3.9+ / Conda

**前端**:
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **HTTP 客户端**: Axios

**未来扩展**: 
- Live2D / Unity 3D
- 语音合成 (VITS / Azure TTS)
- 向量检索 (FAISS / Milvus)

## 当前状态

- ✅ Phase 0: 世界骨架
- 🚧 Phase 1: 对话系统
- 📋 Phase 2: 记忆系统
- 🎨 Phase 3: 表现层
- 🎤 Phase 4: 多模态
