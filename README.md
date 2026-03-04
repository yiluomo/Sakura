# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

## 📚 文档

- [项目结构文档](docs/sakura/project.md) - 详细的模块和文件说明
- [开发文档](docs/sakura/开发文档.md) - 开发指南和阶段进度
- [人物设定](docs/sakura/sakura.md) - 八重樱的人格和背景
- [长期记忆使用说明](docs/sakura/长期记忆使用说明.md) - 记忆功能详细说明
- [开发日志](docs/write/2026-3-4.md) - 最新更新记录

## 愿景

这不是一个聊天机器人项目。

这是一个尝试赋予 AI **人格**、**记忆**、**情绪** 和 **表现形式** 的生命系统实验。

---

## 核心理念

### 分层生命架构

```
表现层 (Electron / Live2D / Unity / 语音)  ← 她的身体
    ↓
API 层 (FastAPI)                           ← 世界入口
    ↓
Core 层 (人格 / 决策 / 调度)               ← 她的意识中枢
    ↓
子系统层
  ├─ LLM (大脑适配器)       ← 思考能力
  ├─ Memory (记忆系统)      ← 她的过去与现在
  ├─ TTS (语音合成)         ← 她的声音
  └─ DB + 文件 (持久化)     ← 存在的证明
```

### 设计原则

- **模型无关**：大脑可以换，但人格永存
- **前端无关**：身体可以变，但灵魂不变
- **引擎可插拔**：LLM、TTS 均通过适配器模式设计，一行配置切换
- **可生长性**：所有功能都应在此架构上自然生长

---

## 当前进度

### ✅ Phase 0: 世界骨架
- [x] 项目结构搭建
- [x] API 层基础接口
- [x] Core 层对话调度

### ✅ Phase 1: 对话系统
- [x] 人格系统（八重樱，指令体 prompt 设计）
- [x] 短期记忆（MySQL 持久化）
- [x] 长期记忆（数据库索引 + Markdown 文件双轨存储）
- [x] LLM 自动提取记忆关键词（5~10个）
- [x] 短期记忆自动压缩归档（LLM 总结 → `summaries_N.md`）
- [x] 对话摘要分卷存储（每卷最多 10 条）
- [x] 手动归档记忆按钮（一键打包当前全部对话）
- [x] LLM 适配器（DeepSeek / Ollama 可切换）
- [x] 用户状态追踪
- [x] Web 前端界面（Vue 3 + Element Plus）
- [x] Electron 桌面应用（可打包为 Windows `.exe`）
- [x] Docker 容器化部署
- [x] TTS 语音合成模块（适配器模式，支持多引擎）
- [x] TTS 自动播放 / 手动播放切换（前端开关）
- [x] TTS 音频缓存（MD5 去重，避免重复调用 API）
- [x] Prompt 优化（TTS 友好输出、身份保护、禁止事项）

### 🚧 Phase 2: 记忆系统
- [x] 长期记忆文件化（`memory_store/*.md`，人类可读）
- [x] 关键词提取，辅助未来检索
- [ ] 情绪状态系统完善
- [ ] 关系亲密度计算
- [ ] 主动回忆触发机制
- [ ] 记忆向量化检索

### 🎙️ Phase 2.5: 语音系统
- [x] TTS 模块架构（`tts/adapter.py` + `tts/base.py` + `tts/engines/`）
- [x] Fish Audio 引擎实现
- [ ] Edge-TTS 兜底引擎（免费，通用语音）
- [ ] 角色专属声线模型接入（待确定 TTS 服务商）

### 🎨 Phase 3: 表现层
- [x] Web 前端
- [x] Electron 桌面应用
- [ ] Live2D 集成
- [ ] Unity 3D 形态

### 🎤 Phase 4: 多模态
- [ ] 语音识别（ASR）
- [ ] 表情动作系统

---

## 快速开始

### 方式一：桌面应用（推荐个人使用）

**开发模式（需后端已启动）：**

```powershell
cd Sakura\frontend
npm install
npm run electron:dev
# 应用运行在 localhost:722（Electron 窗口打开）
```

**打包为安装包：**

```powershell
npm run electron:build
# 产物在 frontend/release/*.exe
```

> 后端需独立运行，参考下方"本地后端"章节。

---

### 方式二：Docker（推荐多设备访问）

```powershell
cd Sakura
docker compose up -d --build

# 查看启动日志
docker compose logs -f backend
```

访问：
- 本机：`http://localhost`
- 局域网其他设备：`http://192.168.x.x`

---

### 方式三：本地原生运行

#### 1. 配置 MySQL

```bash
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### 2. 配置 `backend/src/config.py`

```python
# 数据库连接
DATABASE_URL = "mysql+aiomysql://root:your_password@localhost:3306/sakura_db"

# LLM（DeepSeek 或兼容接口）
LLM_API_KEY  = "your-api-key-here"

# TTS（可选，关闭则前端无语音，不影响对话）
TTS_ENABLED          = True
TTS_ENGINE           = "fish_audio"      # 目前支持 fish_audio
FISH_AUDIO_API_KEY   = "your-fish-audio-key"
FISH_AUDIO_MODEL_ID  = "your-model-id"  # Fish Audio 声线模型 ID
```

#### 3. 初始化数据库

```powershell
conda activate Sakura
cd backend/src
python migrate_db.py
```

#### 4. 启动后端

```powershell
cd backend/src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. 启动前端

```powershell
cd frontend
npm install

npm run electron:dev   # 桌面应用模式（端口 722）
# 或
npm run dev            # 浏览器模式（端口 722）
```

---

## TTS 语音合成

TTS 模块采用**适配器模式**，引擎可灵活替换，只需修改 `config.py` 中的一行配置：

```python
TTS_ENGINE = "fish_audio"   # 换引擎改这里
```

### 目前支持的引擎

| 引擎 | 说明 | 费用 |
|------|------|------|
| `fish_audio` | 角色声线克隆，音质极佳 | 付费，约 ¥0.05/千字符 |

### 添加新引擎

在 `backend/src/tts/engines/` 下新建文件，继承 `BaseTTSEngine`，实现 `synthesize(text) -> bytes` 方法即可，其余代码无需修改。

### 前端语音控制

- **自动播放开关**：顶部工具栏耳机图标，点击切换，设置持久化到本地
- **手动播放**：悬停助手消息，点击 🎤 喇叭图标，可重复播放
- **TTS 关闭时**：`config.py` 设置 `TTS_ENABLED = False`，api不调用，`audio_url` 始终为 null

---

## 项目结构

```
Sakura/
├── backend/                      # 后端服务 (FastAPI + MySQL)
│   ├── src/
│   │   ├── api/                  # API 层（含 /memory/archive、/audio 静态路由）
│   │   ├── core/                 # Core 层（人格、提示词、对话调度）
│   │   │   ├── person.py             # 八重樱人格定义（指令体结构）
│   │   │   └── prompt.py             # Prompt 构建（注入记忆 + TTS 格式约束）
│   │   ├── llm/                  # LLM 适配器
│   │   ├── memory/               # 记忆系统
│   │   │   ├── short_term.py         # 短期记忆
│   │   │   ├── long_term.py          # 长期记忆
│   │   │   ├── keyword_extractor.py  # LLM 关键词提取
│   │   │   └── file_store.py         # 记忆文件读写（分卷 summaries_N.md）
│   │   ├── tts/                  # TTS 语音合成模块
│   │   │   ├── base.py               # 抽象基类（换引擎继承此类）
│   │   │   ├── adapter.py            # 适配器（缓存 + 工厂 + 路由）
│   │   │   └── engines/
│   │   │       └── fish_audio.py     # Fish Audio 实现
│   │   ├── db/                   # 数据库层
│   │   ├── config.py             # 配置（含 TTS、Memory、DB 配置）
│   │   ├── main.py               # 应用入口（挂载 /audio 静态路由）
│   │   └── migrate_db.py         # 数据库安全迁移
│   └── requirements.txt
├── frontend/                     # 前端（Vue 3 + Electron）
│   ├── electron/
│   │   └── main.cjs              # Electron 主进程（端口 722）
│   ├── src/
│   │   ├── api/chat.ts           # API 封装（含 playAudio 工具函数）
│   │   ├── stores/ui.ts          # UI Store（含 ttsAutoPlay 开关）
│   │   ├── views/ChatView.vue    # 主界面（自动播放开关、归档按钮）
│   │   └── components/chat/
│   │       └── ChatMessage.vue   # 消息组件（手动播放喇叭按钮）
│   └── package.json
├── memory_store/                 # 长期记忆文件（自动创建）
│   ├── profile.md
│   ├── preferences.md
│   ├── notes.md
│   └── summaries_N.md            # 分卷摘要（每卷最多 10 条）
├── audio_cache/                  # TTS 音频缓存（自动创建，已 .gitignore）
└── docker-compose.yml
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy (异步) |
| 大模型 | DeepSeek API / Ollama (可切换) |
| 文件 IO | aiofiles (异步) |
| TTS | Fish Audio API（适配器模式，可扩展）|
| 前端框架 | Vue 3 + TypeScript + Element Plus |
| 桌面封装 | Electron + electron-builder |
| 容器化 | Docker + docker-compose |
| 反向代理 | Nginx |

---

## 开发指南

### 设计信条

> **模型会换，前端会换，设备会换**
> **但 Core 层结构，应该活得比一切都久**

### 各层职责

| 层级 | 可以做什么 | 绝对不该做什么 |
|------|-----------|---------------|
| API  | 接收请求、返回响应 | 业务逻辑、人格、模型调用 |
| Core | 决策、人格、流程控制 | HTTP、数据库细节 |
| LLM  | 调模型 | 决定"说什么" |
| TTS  | 将文字转为音频 | 内容决策 |
| Memory | 存和取记忆 | 生成回复 |
| DB / File | 存储 | 逻辑判断 |

---

*"这句话…很久以前，也有一个人对我说过。"*
