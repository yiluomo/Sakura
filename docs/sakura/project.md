# 项目模块结构

## 根目录

```
Sakura/
├── backend/                 # 后端服务
├── frontend/                # 前端界面（含 Electron 桌面应用）
├── docs/                    # 项目文档
├── memory_store/            # 长期记忆 Markdown 文件（运行时自动创建）
├── .git/                    # Git 版本控制
├── .gitignore               # Git 忽略规则
└── README.md                # 项目说明
```

## Backend 模块

```
backend/
├── src/                     # 源代码
├── test/                    # 测试脚本
└── requirements.txt         # Python 依赖清单
```

### src/ - 源代码

```
src/
├── api/                     # API 层 - 世界入口
├── core/                    # Core 层 - 意识中枢
├── llm/                     # LLM 层 - 大脑适配器
├── memory/                  # Memory 层 - 记忆系统
├── db/                      # DB 层 - 持久化
├── models/                  # 数据模型
├── logs/                    # 运行日志目录
├── config.py                # 配置（支持环境变量覆盖）
├── main.py                  # 应用入口
└── migrate_db.py            # 数据库安全迁移脚本
```

#### api/ - API 层

| 文件 | 职责 |
|------|------|
| `chat.py` | 所有业务接口（对话、记忆、TTS、归档） |
| `deps.py` | FastAPI 依赖注入（`verify_token` Token 认证）|
| `__init__.py` | 模块初始化 |

> 所有接口均通过 `deps.verify_token` 保护，请求头需携带 `X-API-Token`。

**API 接口列表：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/history` | 获取对话历史（默认最近 50 条）|
| POST | `/api/chat` | 发送消息，返回回复、情绪、音频 URL |
| POST | `/api/memory` | 手动保存一条记忆 |
| POST | `/api/memory/confirm` | 用户确认/取消记忆保存 |
| POST | `/api/memory/archive` | 手动归档最早 N 条短期记忆到长期记忆 |
| POST | `/api/memory/export` | 导出全部对话记录为 JSON 文件 |
| POST | `/api/memory/import` | 导入记忆 JSON 文件并可选重建向量索引 |
| POST | `/api/tts` | 按需生成 TTS 音频（命中缓存直接返回）|
| POST | `/api/tts/set_refer_audio` | 设置 GPT-SoVITS 参考音频 |
| POST | `/api/tts/set_gpt_weights` | 热切换 GPT 模型权重 |
| POST | `/api/tts/set_sovits_weights` | 热切换 SoVITS 模型权重 |

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
| `short_term.py` | 短期记忆（读写、自动压缩归档、手动强制归档） |
| `long_term.py` | 长期记忆（触发检测、三步写入、读取注入 prompt） |
| `keyword_extractor.py` | LLM 关键词提取（5~10 个，用于记忆检索） |
| `file_store.py` | 记忆文件读写（Markdown，`memory_store/*.md`） |
| `recall.py` | 回忆机制（聚合短期 + 长期记忆） |
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
- `long_term_memory`: 长期记忆索引（memory_type, key, value摘要, keywords, file_path, importance）
- `user_states`: 用户状态（亲密度、情绪）

## memory_store/ - 长期记忆文件

运行时自动创建，存储人类可读的 Markdown 格式记忆。可直接打开查看和手动编辑。

```
memory_store/
├── profile.md         # 个人档案（姓名、年龄、生日、职业、家人、朋友）
├── preferences.md     # 偏好与经历（爱好、厌恶、经历）
├── notes.md           # 通用手动笔记
├── summaries_1.md     # 对话摘要第1卷（1~10条）
├── summaries_2.md     # 对话摘要第2卷（11~20条）
└── summaries_N.md     # 自动增长……（每卷最多10条）
```

每条记忆以 `<!-- entry: type/key -->` 注释作为唯一标识，程序据此定位更新。
对话摘要满10条后自动新建下一卷，所有卷均参与 prompt 注入时的排序和读取。

## Frontend 模块

```
frontend/
├── electron/
│   └── main.js          # Electron 主进程（桌面窗口）
├── src/                 # 源代码
│   ├── api/             # API 接口（含 archiveMemory）
│   ├── asserts/         # 静态资源（图片/视频）
│   ├── components/      # Vue 组件
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia 状态管理
│   ├── styles/          # 样式文件
│   ├── types/           # TypeScript 类型定义
│   └── views/           # 页面视图
├── package.json         # 项目配置（含 Electron 脚本）
├── vite.config.ts       # Vite 配置
└── tsconfig.json        # TypeScript 配置
```

**技术栈**:
- Vue 3 + TypeScript
- Element Plus UI 组件库
- Pinia 状态管理
- Vite 构建工具
- **Electron**（桌面应用封装）

**运行方式**：

| 命令 | 说明 |
|------|------|
| `npm run dev` | Web 开发模式（浏览器） |
| `npm run electron:dev` | 桌面应用开发模式（Electron 热重载） |
| `npm run build` | 构建 Web 静态文件（供 Nginx/Docker） |
| `npm run electron:build` | 打包 Windows 安装包（`release/*.exe`） |

## Docs 模块

```
docs/
├── sakura/             # 项目文档
│   ├── 开发文档.md         # 开发阶段、进度、技术债务
│   ├── project.md          # 本文件：模块结构、接口、数据流
│   ├── sakura.md           # 人物设定
│   ├── 长期记忆使用说明.md
│   ├── 公网部署方案.md      # Cloudflare Tunnel + 安全加固方案（待实施）
│   └── summaries_example.md  # summaries.md 格式示例
└── write/              # 开发日志
    └── ...（按日期）
```

## 数据流

```
用户请求
  ↓
api/chat.py（接收请求）
  ↓
core/conversation.py（对话调度）
  ├─ memory/recall.py          → 回忆上下文（短期DB + 长期文件TopN）
  ├─ core/person.py            → 加载人格
  ├─ core/prompt.py            → 构建提示词（注入长期记忆内容）
  ├─ llm/adapter.py            → 调用 DeepSeek/Ollama 生成回复
  ├─ memory/short_term.py      → 保存对话到DB，达阈值自动压缩归档
  └─ memory/long_term.py       → 检测"记住"触发，返回待确认记忆信息
  ↓
返回 { reply, memory_info }

用户确认保存记忆时：
api/chat.py → POST /api/memory/confirm
  ↓
memory/long_term.py → confirm_save_memory()
  ├─ memory/keyword_extractor.py  → LLM 提取 5~10 个关键词
  ├─ memory/file_store.py         → 写入 memory_store/*.md
  └─ db/crud.py                   → 写入 long_term_memory 索引表

点击"归档记忆"按钮时：
api/chat.py → POST /api/memory/archive
  ↓
memory/short_term.py → force_archive()
  ├─ LLM 总结全部短期记忆
  ├─ memory/keyword_extractor.py  → 提取关键词
  ├─ memory/file_store.py         → 写入 summaries.md
  ├─ db/crud.py                   → 写入数据库索引
  └─ 清空 conversations 表
```

## 数据库结构

```
MySQL: sakura_db
├─ conversations        （短期对话历史）
│  ├─ id
│  ├─ user_id
│  ├─ role (user/assistant)
│  ├─ content
│  └─ timestamp
├─ long_term_memory     （长期记忆轻量索引）
│  ├─ id
│  ├─ memory_type       （name/hobby/manual/conversation_summary 等）
│  ├─ key               （触发关键词，如 "我叫"）
│  ├─ value             （内容摘要，前 100 字）
│  ├─ keywords          （LLM 提取的关键词，逗号分隔）
│  ├─ file_path         （对应 .md 文件路径）
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
- **环境**: Python 3.9+ / uv

**前端**:
- **框架**: Vue 3 + TypeScript
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **桌面封装**: Electron
- **HTTP 客户端**: Axios

**部署**:
- **反向代理**: Nginx（本地）
- **服务化**: NSSM（Windows 原生部署）
- **桌面打包**: electron-builder（Windows NSIS 安装包）

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
