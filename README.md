# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

### 🚀 快速启动

```powershell
# 日常启动
.\start.ps1

# 停止服务
.\start.ps1 -Stop

# 查看状态
.\start.ps1 -Status
```

### 📚 详细文档

- [项目结构文档](docs/sakura/project.md)
- [开发文档](docs/sakura/开发文档.md)
- [人物设定](docs/sakura/sakura.md)
- [长期记忆使用说明](docs/sakura/长期记忆使用说明.md)
- [开发工具指南](dev-tools/README.md)

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
- [x] LLM 适配器（DeepSeek / Ollama 可切换）
- [x] 用户状态追踪
- [x] Web 前端界面（Vue 3 + Element Plus）
- [x] Electron 桌面应用（可打包为 Windows `.exe`）
- [x] Docker 容器化部署
- [x] TTS 语音合成模块（适配器模式，支持多引擎）
- [x] TTS 自动播放 / 手动播放切换（前端开关）
- [x] TTS 音频缓存（MD5 去重，避免重复调用 API）
- [x] Prompt 优化（TTS 友好输出、身份保护、禁止事项）

### ✅ Phase 2: 记忆系统
- [x] 长期记忆文件化（`memory_store/*.md`，人类可读）
- [x] RAG 向量检索（FAISS + OpenAI Embedding）
- [x] 语义相似度检索（理解用户意图）
- [x] 混合记忆召回（短期 + 向量 + 长期）
- [x] 情绪状态系统
- [x] 主动问候机制
- [ ] 关系亲密度计算
- [ ] 情绪衰减定时任务

### 🎙️ Phase 2.5: 语音系统
- [x] TTS 模块架构（`tts/adapter.py` + `tts/base.py` + `tts/engines/`）
- [x] GPT-SoVITS 引擎实现（本地部署，无需联网）
- [ ] Edge-TTS 兜底引擎（免费，通用语音）
- [ ] ASR 语音识别
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

### 前置要求

- **MySQL 8.0+**：数据库
- **Python 3.9+**：后端运行环境
- **Node.js 16+**：前端运行环境
- **Anaconda/Miniconda**（推荐）：Python 虚拟环境管理

### 首次安装步骤

```powershell
# 1. 创建虚拟环境
conda create -n sakura python=3.9 -y
conda activate sakura

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 配置数据库（编辑 backend/src/config.py）
# 修改 DATABASE_URL、LLM_API_KEY 等配置

# 4. 创建数据库
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 5. 初始化数据库
cd src
python init_db.py

# 6. 启动后端
cd ../..
.\start.ps1
```

### 日常启动步骤

```powershell
# 1. 激活环境
conda activate sakura

# 2. 启动所有服务
.\start.ps1
```

---

### 方式一：桌面应用（推荐个人使用）

#### 1. 配置并启动后端

```bash
# 激活虚拟环境
conda activate sakura

# 配置数据库和 API Key
# 编辑 backend/src/config.py

# 数据库迁移（首次运行或升级时）
cd backend/src
python migrate_and_index.py

# 启动后端
python main.py
```

#### 2. 启动前端（桌面应用）

```powershell
cd frontend
npm install

# 开发模式（热重载）
npm run electron:dev

# 或打包为安装包
npm run electron:build
# 产物在 frontend/release/*.exe
```

---

### 方式二：Docker（推荐多设备访问）

```bash
cd Sakura
docker compose up -d --build

# 查看启动日志
docker compose logs -f backend
```

**访问：**
- 本机：`http://localhost`
- 局域网其他设备：`http://192.168.x.x`

---

### 方式三：本地原生运行（完整控制）

#### 1. 配置 MySQL

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### 2. 配置 `backend/src/config.py`

```python
# 数据库连接
DATABASE_URL = "mysql+aiomysql://root:your_password@localhost:3306/sakura_db"

# LLM（DeepSeek 或兼容接口）
LLM_API_KEY  = "your-api-key-here"
LLM_API_BASE = "https://api.deepseek.com/v1"

# Embedding（用于向量检索，可使用 LLM 的 key）
EMBEDDING_API_KEY = "your-api-key-here"
EMBEDDING_MODEL = "text-embedding-3-small"

# TTS（可选，关闭则前端无语音，不影响对话）
TTS_ENABLED = True
TTS_ENGINE = "gpt_sovits"
GPT_SOVITS_BASE_URL = "http://127.0.0.1:9872"
GPT_SOVITS_REF_AUDIO_PATH = r"C:\path\to\reference.wav"
```

#### 3. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 4. 初始化数据库

```powershell
conda activate sakura
cd backend/src
python init_db.py
```

#### 5. 启动后端

```powershell
conda activate sakura
cd backend/src
python main.py
```

#### 6. 启动前端

```powershell
cd frontend
npm install
npm run electron:dev
```

---

## 数据库管理

### 全新安装

```bash
# 1. 创建数据库
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 初始化表结构
cd backend/src
python init_db.py
```

### 升级现有系统

```bash
cd backend/src
python migrate_and_index.py
```

**功能：**
- ✅ 迁移数据库结构（conversations + user_states）
- ✅ 为所有旧对话生成向量索引
- ✅ 不删除任何数据

**运行前确保：**
1. MySQL 已启动
2. Qdrant 已启动（`.\start_qdrant.ps1`）
3. 配置了 `EMBEDDING_API_KEY`

### 记忆导出与导入（备份/迁移）

#### 导出记忆

通过 API 导出所有对话记录为 JSON 文件：

```bash
# 方式一：使用 curl
curl -X POST "http://localhost:8000/api/memory/export?user_id=依洛沐" \
  --output memory_backup.json

# 方式二：浏览器访问（会自动下载）
# http://localhost:8000/api/memory/export?user_id=依洛沐
```

**导出内容：**
- MySQL 中的所有对话记录（包含情绪、重要度、时间戳等）
- 导出时间和统计信息

**注意：**
- Qdrant 向量数据不导出（可以从 MySQL 重建）
- `memory_store/*.md` 文件需要手动备份

#### 导入记忆

通过 API 导入之前导出的 JSON 文件：

```bash
# 使用 curl
curl -X POST "http://localhost:8000/api/memory/import?user_id=依洛沐&rebuild_vectors=true&skip_existing=true" \
  -F "file=@memory_backup.json"
```

**参数说明：**
- `user_id`: 用户 ID
- `rebuild_vectors`: 是否重建向量索引（默认 true）
- `skip_existing`: 是否跳过已存在的记录（默认 true，避免重复导入）

**导入流程：**
1. 上传导出的 JSON 文件
2. 将对话记录导入 MySQL
3. 自动重建 Qdrant 向量索引

#### 使用场景

**场景一：定期备份**
```bash
# 每周导出一次
curl -X POST "http://localhost:8000/api/memory/export?user_id=依洛沐" \
  --output backup_$(date +%Y%m%d).json
```

**场景二：更换设备**

在旧设备上：
```bash
# 1. 导出对话记录
curl -X POST "http://localhost:8000/api/memory/export?user_id=依洛沐" \
  --output memory_backup.json

# 2. 备份数据库（可选，双重保险）
mysqldump -u root -p sakura_db > sakura_backup.sql

# 3. 备份记忆文件
# 复制 memory_store/ 目录
```

在新设备上：
```bash
# 1. 创建数据库
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 初始化表结构
cd backend/src
python init_db.py

# 3. 导入对话记录（推荐）
curl -X POST "http://localhost:8000/api/memory/import?user_id=依洛沐&rebuild_vectors=true" \
  -F "file=@memory_backup.json"

# 或者：恢复数据库备份 + 重建向量
mysql -u root -p sakura_db < sakura_backup.sql
python migrate_and_index.py

# 4. 恢复记忆文件
# 将 memory_store/ 目录复制到项目根目录
```

**场景三：灾难恢复**

如果 Qdrant 向量数据丢失：
```bash
# 从 MySQL 重建所有向量索引
cd backend/src
python migrate_and_index.py
```

如果 MySQL 数据丢失但有导出文件：
```bash
# 导入备份文件
curl -X POST "http://localhost:8000/api/memory/import?user_id=依洛沐&rebuild_vectors=true" \
  -F "file=@memory_backup.json"
```

---

## 验证部署

### 检查服务状态

```bash
# 1. 检查 MySQL
mysql -u root -p -e "USE sakura_db; SHOW TABLES;"

# 2. 检查后端
curl http://localhost:8000/

# 3. 测试对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "你好"}'
```

### 验证向量检索

```bash
# 发送第一条消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "我喜欢樱花"}'

# 等待几秒（向量生成是异步的）

# 发送相关消息，应该能召回之前的对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "还记得我们聊过花吗？"}'
```

---

# 或使用标准迁移
python migrate_db.py
```

#### 6. 启动后端

```powershell
cd backend/src
python main.py

# 或使用 uvicorn
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动成功日志：**
```
[INFO] 数据库初始化完成
✅ Qdrant 集合已存在: conversations
[INFO] Qdrant 向量数据库初始化完成
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 7. 启动前端

```powershell
cd frontend
npm install

npm run electron:dev   # 桌面应用模式（端口 722）
# 或
npm run dev            # 浏览器模式（端口 722）
```

---

## RAG 向量检索记忆系统

### 核心特性

- **语义理解**：不依赖关键词，理解用户真实意图
- **保留所有对话**：不再压缩删除，所有对话永久保存
- **混合召回**：短期记忆 + 向量检索 + 长期记忆
- **异步生成**：向量生成不阻塞对话，用户体验流畅

### 记忆分层

```
用户消息："还记得我们聊过樱花吗？"
  ↓
1. 短期记忆（最近 6 轮对话）
   - 用于上下文连贯
   
2. 向量记忆（语义相似的 5 条对话）
   - [2026-03-05] 今天樱花开了
   - [2026-03-06] 春天到了
   
3. 长期记忆（手动标记的重要信息）
   - 姓名：依洛沐
   - 生日：3月15日
```

### 技术实现

- **向量存储**：FAISS（本地文件，无需服务）
- **Embedding 模型**：OpenAI API / DeepSeek（可配置）
- **相似度算法**：余弦相似度（Cosine Similarity）
- **数据安全**：MySQL 是唯一数据源，向量可随时重建

### 存储成本

| 时间 | 对话数 | MySQL | FAISS | 总计 |
|------|--------|-------|-------|------|
| 1 年 | 72,000 | 11 MB | 110 MB | 121 MB |
| 3 年 | 216,000 | 32 MB | 330 MB | 362 MB |
| 5 年 | 360,000 | 54 MB | 550 MB | 604 MB |

**结论**：存储成本完全可控，3 年 < 400 MB

### 快速部署

```bash
# 1. 安装依赖
pip install faiss-cpu numpy openai

# 2. 数据库迁移
python backend/src/migrate_and_index.py

# 3. 启动应用
.\start.ps1
```

---

## TTS 语音合成

TTS 模块采用**适配器模式**，引擎可灵活替换，只需修改 `config.py` 中的一行配置：

```python
TTS_ENGINE = "gpt_sovits"   # 换引擎改这里
```

### 目前支持的引擎

| 引擎 | 说明 | 费用 |
|------|------|------|
| `gpt_sovits` | 本地推理，音色克隆，无需联网 | 免费（需本地部署 GPT-SoVITS）|

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
│   │   │   ├── vector_store.py       # 向量数据库管理
│   │   │   ├── recall.py             # 混合记忆召回
│   │   │   ├── keyword_extractor.py  # LLM 关键词提取
│   │   │   └── file_store.py         # 记忆文件读写
│   │   ├── tts/                  # TTS 语音合成模块
│   │   │   ├── base.py               # 抽象基类（换引擎继承此类）
│   │   │   ├── adapter.py            # 适配器（缓存 + 工厂 + 路由）
│   │   │   └── engines/
│   │   │       └── gpt_sovits.py     # GPT-SoVITS 引擎实现
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
│   ├── profile.md                # 个人档案
│   ├── preferences.md            # 偏好与经历
│   ├── notes.md                  # 手动笔记
│   └── vectors/                  # FAISS 向量索引
│       ├── conversations.index   # 向量数据
│       ├── metadata.json         # 元数据
│       └── id_mapping.json       # ID 映射
├── audio_cache/                  # TTS 音频缓存（自动创建，已 .gitignore）
└── docker-compose.yml
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy (异步) |
| 向量存储 | FAISS (本地文件) |
| 大模型 | DeepSeek API / Ollama (可切换) |
| Embedding | OpenAI API / DeepSeek (向量生成) |
| 文件 IO | aiofiles (异步) |
| TTS | GPT-SoVITS（本地部署，适配器模式，可扩展）|
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
