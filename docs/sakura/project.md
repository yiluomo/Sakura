# 项目模块结构

## 根目录

```
Sakura/
├── backend/          # 后端服务
├── frontend/         # 前端界面
├── docs/             # 项目文档
├── memory_store/     # 长期记忆 Markdown 文件（运行时自动创建）
├── docker-compose.yml  # Docker 容器编排
├── .git/             # Git 版本控制
├── .gitignore        # Git 忽略规则
└── README.md         # 项目说明
```

## Backend 模块

```
backend/
├── src/              # 源代码
├── test/             # 测试脚本
├── Dockerfile        # Docker 镜像构建
├── entrypoint.sh     # 容器启动脚本
├── requirements.txt  # Python 依赖
└── environment.yml   # Conda 环境配置
```

### src/ - 源代码

```
src/
├── api/              # API 层 - 世界入口
├── core/             # Core 层 - 意识中枢
├── llm/              # LLM 层 - 大脑适配器
├── memory/           # Memory 层 - 记忆系统
├── db/               # DB 层 - 持久化
├── models/           # 数据模型
├── logs/             # 运行日志目录
├── config.py         # 配置文件（支持环境变量覆盖）
├── main.py           # 应用入口
└── migrate_db.py     # 数据库表结构迁移脚本
```

#### api/ - API 层

| 文件 | 职责 |
|------|------|
| `chat.py` | 对话、记忆保存与确认接口 |
| `__init__.py` | 模块初始化 |

#### core/ - Core 层

| 文件 | 职责 |
|------|------|
| `conversation.py` | 对话调度器（主流水线） |
| `person.py` | 人格系统 |
| `prompt.py` | 提示词构建 |
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
| `short_term.py` | 短期记忆（对话历史读写、自动压缩归档） |
| `long_term.py` | 长期记忆（触发检测、写入文件+数据库、读取注入） |
| `keyword_extractor.py` | LLM 关键词提取（5~10个，用于记忆检索） |
| `file_store.py` | 记忆文件读写（Markdown，`memory_store/*.md`） |
| `recall.py` | 回忆机制（聚合短期+长期记忆） |
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
- `conversations`: 对话历史（user_id, role, content, timestamp）
- `long_term_memory`: 长期记忆索引（memory_type, key, keywords, file_path, importance）
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

## memory_store/ - 长期记忆文件

运行时自动创建，存储人类可读的 Markdown 格式记忆。

```
memory_store/
├── profile.md       # 个人信息（姓名、年龄、生日、工作、家人、朋友）
├── preferences.md   # 偏好信息（爱好、厌恶、经历）
├── notes.md         # 通用手动笔记
└── summaries.md     # 对话压缩自动归档摘要
```

每条记忆以 `<!-- entry: type/key -->` 注释作为唯一标识，程序据此定位更新。

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
│   └── views/       # 页面视图
├── Dockerfile       # Docker 镜像构建（多阶段）
├── nginx.docker.conf # 容器内 Nginx 配置
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
├── sakura/          # 项目文档
│   ├── 开发文档.md
│   ├── project.md        # 本文件
│   ├── sakura.md
│   └── 长期记忆使用说明.md
└── write/           # 写作文档
```

## 数据流

```
用户请求
  ↓
api/chat.py（接收请求）
  ↓
core/conversation.py（对话调度）
  ├─ memory/recall.py          → 回忆上下文（短期DB + 长期文件）
  ├─ core/person.py            → 加载人格
  ├─ core/prompt.py            → 构建提示词（注入长期记忆关键词）
  ├─ llm/adapter.py            → 调用 DeepSeek/Ollama 生成回复
  ├─ memory/short_term.py      → 保存对话到DB，达阈值自动压缩归档
  └─ memory/long_term.py       → 检测"记住"触发，返回待确认记忆信息
  ↓
返回 { reply, memory_info }

用户确认保存记忆时：
api/chat.py → /memory/confirm
  ↓
memory/long_term.py → confirm_save_memory()
  ├─ memory/keyword_extractor.py  → LLM 提取 5~10 个关键词
  ├─ memory/file_store.py         → 写入 memory_store/*.md
  └─ db/crud.py                   → 写入 long_term_memory 索引表
```

## 数据库结构

```
MySQL: sakura_db
├─ conversations        （对话历史）
│  ├─ id
│  ├─ user_id
│  ├─ role (user/assistant)
│  ├─ content
│  └─ timestamp
├─ long_term_memory     （长期记忆索引）
│  ├─ id
│  ├─ memory_type       （name/hobby/manual/conversation_summary 等）
│  ├─ key               （触发关键词，如 "我叫"）
│  ├─ value             （内容摘要，前100字）
│  ├─ keywords          （LLM提取的关键词，逗号分隔）
│  ├─ file_path         （对应 .md 文件路径，如 "memory_store/profile.md"）
│  ├─ importance        （重要度 1~5）
│  └─ created_at/updated_at
└─ user_states          （用户状态）
   ├─ user_id（主键）
   ├─ affinity（亲密度）
   ├─ mood（情绪）
   ├─ last_interaction
   └─ total_messages
```

## 技术栈

**后端**:
- **框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy (异步)
- **大模型**: DeepSeek API / Ollama
- **HTTP 客户端**: httpx (异步)
- **文件 IO**: aiofiles (异步)
- **环境**: Python 3.9+ / Conda

**前端**:
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **HTTP 客户端**: Axios

**部署**:
- **容器化**: Docker + docker-compose
- **反向代理**: Nginx（容器内托管前端 + 代理后端）
- **服务化**: NSSM（Windows 原生部署）

**未来扩展**: 
- Live2D / Unity 3D
- 语音合成 (VITS / Azure TTS)
- 向量检索 (FAISS / Milvus)

## 当前状态

- ✅ Phase 0: 世界骨架
- ✅ Phase 1: 对话系统
- 🚧 Phase 2: 记忆系统（进行中）
- 🎨 Phase 3: 表现层
- 🎤 Phase 4: 多模态
