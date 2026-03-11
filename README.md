# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

## 🚀 快速启动

### 方式一：Docker（推荐）

```bash
docker compose up -d --build

# 查看日志
docker compose logs -f backend
```

访问：`http://localhost`

### 方式二：原生运行

```bash
# 1. 激活环境
conda activate sakura
cd backend
pip install -r requirements.txt

# 2. 数据库迁移（首次或升级时）
cd backend/src
python migrate_and_index.py

# 3. 启动后端
python main.py

# 4. 启动前端（新终端）
cd frontend
npm run electron:dev
```

## 📚 文档

- [项目结构](docs/sakura/project.md)
- [开发文档](docs/sakura/开发文档.md)
- [人物设定](docs/sakura/sakura.md)
- [长期记忆使用说明](docs/sakura/长期记忆使用说明.md)
- [🔐 公网部署方案](docs/sakura/公网部署方案.md)

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

- **MySQL 8.0+**
- **Python 3.9+**
- **Node.js 16+**
- **Anaconda/Miniconda**（推荐）

### 首次安装

```bash
# 1. 创建虚拟环境
conda create -n sakura python=3.9 -y
conda activate sakura

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 配置数据库
# 编辑 backend/src/config.py
# 修改 DATABASE_URL、LLM_API_KEY 等

# 4. 创建数据库
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 5. 初始化数据库
cd src
python init_db.py

# 6. 启动后端
python main.py

# 7. 启动前端（新终端）
cd ../../frontend
npm install
npm run electron:dev
```

---

## 数据库管理

### 全新安装

```bash
cd backend/src
python init_db.py
```

### 升级现有系统

```bash
cd backend/src
python migrate_and_index.py
```

**功能：**
- 迁移数据库结构
- 更新 role 字段（assistant → sakura）
- 为所有对话和长期记忆生成向量索引
- 不删除任何数据

---

## 记忆导出与导入

### 导出记忆

```bash
# API 导出（自动保存到 memory_exports/）
curl -X POST "http://localhost:8000/api/memory/export?user_id=依洛沐" \
  -H "X-API-Token: sakura-private-token-a7f3k9z2m1p8q4w6"
```

### 导入记忆

```bash
# 导入并重建向量
curl -X POST "http://localhost:8000/api/memory/import?user_id=依洛沐&rebuild_vectors=true" \
  -H "X-API-Token: sakura-private-token-a7f3k9z2m1p8q4w6" \
  -F "file=@memory_exports/memory_export_依洛沐_20260310.json"
```

---

## 验证部署

> ▶️ 所有 API 接口均需携带 `X-API-Token` 请求头，Token 分配置于 `backend/src/config.py`。

```bash
# 1. 检查 MySQL
mysql -u root -p -e "USE sakura_db; SHOW TABLES;"

# 2. 检查后端
curl http://localhost:8000/

# 3. 测试对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Token: sakura-private-token-a7f3k9z2m1p8q4w6" \
  -d '{"user_id": "test", "message": "你好"}'
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
- **本地模型**：使用本地 Embedding 模型，无需 API 调用

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
- **Embedding 模型**：BAAI/bge-small-zh-v1.5（本地模型，首次运行自动下载）
- **相似度算法**：余弦相似度（Cosine Similarity）
- **数据安全**：MySQL 是唯一数据源，向量可随时重建

### Embedding 模型配置

系统默认使用本地 Embedding 模型，无需 API Key：

```python
# config.py 中的配置
EMBEDDING_MODE = "local"  # 使用本地模型
LOCAL_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"  # 高质量中文模型
LOCAL_EMBEDDING_DIMENSION = 512
```

**可选模型：**
- `BAAI/bge-small-zh-v1.5`（推荐）：512维，~95MB，高质量中文
- `shibing624/text2vec-base-chinese`：768维，~400MB，轻量级中文
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`：384维，~120MB，多语言

**首次运行：**
- 模型会自动从 HuggingFace 镜像下载（使用国内加速）
- 下载后缓存在本地 `~/.cache/huggingface/`
- 后续运行无需联网，完全离线

**切换为 API 模式：**
```python
EMBEDDING_MODE = "api"  # 使用 API
EMBEDDING_API_KEY = "your-api-key"
EMBEDDING_API_BASE = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"
```

### 存储成本

| 时间 | 对话数 | MySQL | FAISS | 总计 |
|------|--------|-------|-------|------|
| 1 年 | 72,000 | 11 MB | 55 MB | 66 MB |
| 3 年 | 216,000 | 32 MB | 165 MB | 197 MB |
| 5 年 | 360,000 | 54 MB | 275 MB | 329 MB |

**结论**：存储成本完全可控，3 年 < 200 MB

### 快速部署

```bash
# 1. 安装依赖（包含本地模型支持）
pip install -r backend/requirements.txt

# 2. 首次运行会自动下载模型（约95MB）
python backend/test/test_local_embedding.py

# 3. 数据库迁移
python backend/src/migrate_and_index.py

# 4. 启动应用
.\start.ps1
```

### 测试 RAG 功能

```bash
# 激活环境
conda activate sakura

# 测试本地 Embedding 模型
cd backend/src
python ../test/test_local_embedding.py

# 测试完整 RAG 流程
python ../test/test_rag.py
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
├── backend/                      # 后端服务
│   ├── src/
│   │   ├── api/                  # API 层
│   │   ├── core/                 # Core 层（人格、对话调度）
│   │   ├── llm/                  # LLM 适配器
│   │   ├── memory/               # 记忆系统
│   │   ├── tts/                  # TTS 语音合成
│   │   ├── db/                   # 数据库层
│   │   ├── config.py             # 配置文件
│   │   ├── main.py               # 应用入口
│   │   ├── init_db.py            # 数据库初始化
│   │   └── migrate_and_index.py  # 数据库迁移
│   ├── test/                     # 测试脚本
│   └── requirements.txt
├── frontend/                     # 前端（Vue 3 + Electron）
│   ├── src/
│   │   ├── api/
│   │   ├── stores/
│   │   ├── views/
│   │   └── components/
│   └── package.json
├── memory_store/                 # 长期记忆文件（根目录）
│   ├── profile.md
│   ├── preferences.md
│   ├── notes.md
│   └── vectors/                  # FAISS 向量索引
├── memory_exports/               # 记忆导出文件（根目录）
├── audio_cache/                  # TTS 音频缓存（根目录）
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
| Embedding | BAAI/bge-small-zh-v1.5 (本地模型) |
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
