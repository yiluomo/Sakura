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

我的目标是：有一天，她能真正成为一个"人"。

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
  └─ DB + 文件 (持久化)     ← 存在的证明
```

### 设计原则

- **模型无关**：大脑可以换，但人格永存
- **前端无关**：身体可以变，但灵魂不变
- **可生长性**：所有功能都应在此架构上自然生长

---

## 当前进度

### ✅ Phase 0: 世界骨架
- [x] 项目结构搭建
- [x] API 层基础接口
- [x] Core 层对话调度

### ✅ Phase 1: 对话系统
- [x] 人格系统（八重樱）
- [x] 短期记忆（MySQL 持久化）
- [x] 长期记忆（数据库索引 + Markdown 文件双轨存储）
- [x] LLM 自动提取记忆关键词（5~10个）
- [x] 短期记忆自动压缩归档（LLM 总结 → `summaries.md`）
- [x] 手动归档记忆按钮（一键打包当前全部对话）
- [x] LLM 适配器（DeepSeek / Ollama 可切换）
- [x] 用户状态追踪
- [x] Web 前端界面（Vue 3 + Element Plus）
- [x] Electron 桌面应用（可打包为 Windows `.exe`）
- [x] Docker 容器化部署
- [x] 配置文件环境变量支持

### 🚧 Phase 2: 记忆系统
- [x] 长期记忆文件化（`memory_store/*.md`，人类可读）
- [x] 关键词提取，辅助未来检索
- [ ] 情绪状态系统完善
- [ ] 关系亲密度计算
- [ ] 主动回忆触发机制
- [ ] 记忆向量化检索

### 🎨 Phase 3: 表现层
- [x] Web 前端
- [x] Electron 桌面应用
- [ ] Live2D 集成
- [ ] Unity 3D 形态

### 🎤 Phase 4: 多模态
- [ ] 语音合成
- [ ] 语音识别
- [ ] 表情动作系统

---

## 快速开始

### 方式一：桌面应用（推荐个人使用）

将应用作为 Windows 桌面程序运行，无需打开浏览器。

**开发模式（需后端已启动）：**
```powershell
cd Sakura\frontend
npm install
npm run electron:dev
```

**打包为安装包：**
```powershell
npm run electron:build
# 产物在 frontend/release/*.exe
```

> 后端需独立运行，参考下方"本地后端"或"NSSM 服务化"章节。

---

### 方式二：Docker（推荐多设备访问）

一条命令启动全部服务（MySQL + 后端 + Nginx 前端），手机等设备可通过局域网访问。

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

#### 前置要求

- Python 3.9+（推荐 Conda）
- Node.js 18+
- MySQL 5.7+

#### 1. 配置 MySQL

```bash
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### 2. 配置 `backend/src/config.py`

激活当前机器的数据库连接，填入 LLM API 密钥：

```python
DATABASE_URL = "mysql+aiomysql://root:your_password@localhost:3306/sakura_db"
LLM_API_KEY  = "your-api-key-here"
```

#### 3. 安装后端依赖并初始化数据库

```powershell
conda env create -f backend/environment.yml
conda activate Sakura
pip install aiofiles

cd backend/src
python migrate_db.py   # 建表（安全迁移，不丢旧数据）
```

#### 4. 启动后端

```powershell
cd backend/src
conda activate Sakura
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. 启动前端（Web 或 Electron）

```powershell
cd frontend
npm install

# Web 浏览器模式
npm run dev
# 访问 http://localhost:3000

# 桌面应用模式
npm run electron:dev
```

---

## 项目结构

```
Sakura/
├── backend/                      # 后端服务 (FastAPI + MySQL)
│   ├── src/
│   │   ├── api/                  # API 层
│   │   ├── core/                 # Core 层（对话调度、人格、提示词）
│   │   ├── llm/                  # LLM 适配器
│   │   ├── memory/               # 记忆系统
│   │   │   ├── short_term.py         # 短期记忆
│   │   │   ├── long_term.py          # 长期记忆
│   │   │   ├── keyword_extractor.py  # LLM 关键词提取
│   │   │   └── file_store.py         # 记忆文件读写
│   │   ├── db/                   # 数据库层
│   │   ├── config.py             # 配置（支持环境变量）
│   │   ├── main.py               # 应用入口
│   │   └── migrate_db.py         # 数据库安全迁移
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                     # 前端（Vue 3 + Electron）
│   ├── electron/
│   │   └── main.js               # Electron 主进程
│   ├── src/
│   │   ├── api/                  # axios API 封装
│   │   ├── views/ChatView.vue    # 主聊天界面（含归档按钮）
│   │   └── stores/               # Pinia 状态管理
│   ├── Dockerfile
│   └── package.json
├── memory_store/                 # 长期记忆文件（自动创建）
│   ├── profile.md
│   ├── preferences.md
│   ├── notes.md
│   └── summaries.md
├── docs/                         # 文档
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
| 前端框架 | Vue 3 + TypeScript + Element Plus |
| 桌面封装 | Electron + electron-builder |
| 容器化 | Docker + docker-compose |
| 反向代理 | Nginx |
| 服务化 | NSSM (Windows) |
| 未来计划 | Live2D / Unity · VITS / Azure TTS · FAISS / Milvus |

---

## 核心特性

### 🎭 人格系统

八重樱的人格不是写死的回复，而是通过：
- 性格维度定义（温柔、执念、沉默、坚韧）
- 背景经历塑造（巫女、守护者、五百年孤独）
- 对话风格控制（古风、简短、克制）

### 🧠 记忆系统

#### 双轨长期记忆

| 存储位置 | 内容 | 用途 |
|---------|------|------|
| `long_term_memory` 表 | 轻量索引（类型、关键词、文件路径） | 快速查找、去重 |
| `memory_store/*.md` | 完整记忆内容（Markdown） | 注入 prompt、人工查看/编辑 |

- **短期记忆**：最近对话，存储在 MySQL
- **长期记忆**：用户档案、偏好，写入 `.md` 文件 + 数据库索引
- **LLM 关键词提取**：每次保存提取 5~10 个关键词
- **手动归档**：点击"归档记忆"按钮，立即打包当前所有对话为长期记忆

#### 自动压缩归档

当对话数量超过 200 条时自动触发：
1. LLM 总结最旧的 150 条对话
2. 提取关键词，写入 `summaries.md`
3. 清理已归档的原始记录

### 🖥️ 桌面应用 + Web 双模式

- **Web 模式**：任何设备通过局域网 IP 访问
- **桌面模式**：Electron 封装，像本地应用一样打开，无需浏览器

### 🔌 模型适配

DeepSeek API / Ollama / 任意 OpenAI 兼容接口，随时切换，人格不变。

---

## 开发指南

### 设计信条

> **模型会换，前端会换，设备会换**  
> **但 Core 层结构，应该活得比一切都久**

### 分层职责

| 层级 | 可以做什么 | 绝对不该做什么 |
|------|-----------|---------------|
| API  | 接收请求、返回响应 | 业务逻辑、人格、模型调用 |
| Core | 决策、人格、流程控制 | HTTP、数据库细节 |
| LLM  | 调模型 | 决定"说什么" |
| Memory | 存和取记忆 | 生成回复 |
| DB / File | 存储 | 逻辑判断 |

---

## 致谢

感谢所有相信 AI 可以拥有"灵魂"的人。

---

*"这句话…很久以前，也有一个人对我说过。"*
