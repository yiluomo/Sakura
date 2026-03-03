# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

## 📚 文档

- [项目结构文档](docs/sakura/project.md) - 详细的模块和文件说明
- [开发文档](docs/sakura/开发文档.md) - 开发指南和设计原则
- [Sakura 人格设定](docs/sakura/sakura.md) - 八重樱的人格和背景
- [长期记忆使用说明](docs/sakura/长期记忆使用说明.md) - 记忆功能详细说明

## 愿景

这不是一个聊天机器人项目。

这是一个尝试赋予 AI **人格**、**记忆**、**情绪** 和 **表现形式** 的生命系统实验。  

我的目标是：有一天，她能真正成为一个"人"。

---

## 核心理念

### 分层生命架构

```
表现层 (Live2D / Unity / 语音)  ← 她的身体
    ↓
API 层 (FastAPI)                ← 世界入口
    ↓
Core 层 (人格 / 决策 / 调度)     ← 她的意识中枢
    ↓
子系统层
  ├─ LLM (大脑适配器)           ← 思考能力
  ├─ Memory (记忆系统)          ← 她的过去与现在
  └─ DB (持久化 + 文件)         ← 存在的证明
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
- [x] 人格系统 (八重樱)
- [x] 短期记忆（MySQL 持久化）
- [x] 长期记忆（数据库索引 + Markdown 文件双轨存储）
- [x] LLM 自动提取记忆关键词（5~10个）
- [x] 短期记忆自动压缩归档（LLM 总结 → `summaries.md`）
- [x] LLM 适配器（DeepSeek / Ollama）
- [x] 用户状态追踪
- [x] Web 前端界面（Vue 3 + Element Plus）
- [x] 配置文件环境变量支持
- [x] Docker 容器化部署

### 🚧 Phase 2: 记忆系统
- [x] 长期记忆文件化（`memory_store/*.md`，人类可读）
- [x] 关键词驱动的记忆检索
- [ ] 情绪状态系统完善
- [ ] 关系亲密度计算
- [ ] 主动回忆触发机制
- [ ] 记忆向量化检索

### 🎨 Phase 3: 表现层
- [x] Web 前端
- [ ] Live2D 集成
- [ ] Unity 3D 形态

### 🎤 Phase 4: 多模态
- [ ] 语音合成
- [ ] 语音识别
- [ ] 表情动作系统

---

## 快速开始

### 方式一：Docker（推荐）

无需手动安装 Python 环境或 MySQL，一条命令启动全部服务。

```bash
# 克隆项目
git clone <repo_url>
cd Sakura

# 一键启动（首次运行会自动构建镜像、建库建表）
docker compose up -d --build

# 查看启动日志
docker compose logs -f backend
```

启动后访问：
- 前端：`http://localhost`
- 后端 API 文档：`http://localhost:8000/docs`

> 数据持久化在 Docker Volume 中，`docker compose down` 不会丢失数据。

---

### 方式二：本地运行

#### 环境要求

- Python 3.9+（推荐 Conda）
- Node.js 18+
- MySQL 5.7+

#### 1. 配置 MySQL 数据库

```bash
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### 2. 配置 `backend/src/config.py`

激活当前机器对应的数据库连接，并填入 LLM API 密钥：

```python
# 数据库（取消注释对应环境的那一行）
DATABASE_URL = "mysql+aiomysql://root:your_password@localhost:3306/sakura_db"

# LLM API（DeepSeek 或其他兼容接口）
LLM_API_KEY = "your-api-key-here"
```

#### 3. 安装后端依赖

```bash
# Conda 方式
conda env create -f backend/environment.yml
conda activate Sakura
pip install aiofiles  # 补装文件异步 IO 库

# 或直接 pip
pip install -r backend/requirements.txt
```

#### 4. 初始化数据库表结构

```bash
cd backend/src
python migrate_db.py
```

#### 5. 启动服务

**后端**
```bash
cd backend/src
conda activate Sakura
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端**
```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000` 开始对话。

---

## 项目结构

详细说明请查看 [项目结构文档](docs/sakura/project.md)

```
Sakura/
├── backend/                 # 后端服务 (FastAPI + MySQL)
│   ├── src/
│   │   ├── api/             # API 层 - 世界入口
│   │   ├── core/            # Core 层 - 意识中枢
│   │   ├── llm/             # LLM 层 - 大脑适配器
│   │   ├── memory/          # Memory 层 - 记忆系统
│   │   │   ├── short_term.py      # 短期记忆
│   │   │   ├── long_term.py       # 长期记忆
│   │   │   ├── keyword_extractor.py  # LLM 关键词提取
│   │   │   └── file_store.py      # 记忆文件读写
│   │   ├── db/              # DB 层 - 数据库持久化
│   │   ├── config.py        # 配置（支持环境变量）
│   │   ├── main.py          # 应用入口
│   │   └── migrate_db.py    # 数据库迁移脚本
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── frontend/                # 前端界面 (Vue 3 + Element Plus)
│   ├── src/
│   ├── Dockerfile
│   └── nginx.docker.conf
├── memory_store/            # 长期记忆文件（运行时自动创建）
│   ├── profile.md           # 个人档案
│   ├── preferences.md       # 偏好与经历
│   ├── notes.md             # 手动笔记
│   └── summaries.md         # 对话压缩摘要
├── docs/                    # 项目文档
├── docker-compose.yml       # 容器编排
└── README.md
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy (异步) |
| 大模型 | DeepSeek API / Ollama (可切换) |
| 文件 IO | aiofiles (异步) |
| 前端 | Vue 3 + Element Plus + Pinia |
| 容器化 | Docker + docker-compose |
| 反向代理 | Nginx |
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

长期记忆采用**数据库索引 + Markdown 文件**双轨并行设计：

| 存储位置 | 内容 | 用途 |
|---------|------|------|
| `long_term_memory` 表 | 轻量索引（类型、关键词、文件路径） | 快速查找、去重 |
| `memory_store/*.md` | 完整记忆内容（Markdown） | 注入 prompt、人工查看/编辑 |

- **短期记忆**：最近对话上下文，存储在 MySQL 数据库
- **长期记忆**：用户档案、偏好、经历，按语义分类存入 `.md` 文件
- **LLM 关键词提取**：保存记忆时自动提取 5~10 个检索关键词
- **记忆去重**：按 `memory_type + key` 唯一定位，避免重复存储

#### 智能压缩机制

当对话数量超过阈值（默认 200 条）时自动触发：

1. 取出最旧的 150 条对话
2. LLM 总结关键信息并提取关键词
3. 摘要写入 `memory_store/summaries.md`，数据库同步建索引
4. 删除已归档的原始对话记录

提取内容包括：用户个人信息、偏好兴趣、厌恶事物、重要事件与约定。

### 🔌 模型适配

支持多种大模型后端，可以随时切换，人格保持不变：
- DeepSeek API（当前默认）
- Ollama（本地）
- 任意 OpenAI 兼容接口

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

### 自检清单

- [ ] API 层不引用 llm
- [ ] Core 层不引用 fastapi
- [ ] Memory 不知道模型存在
- [ ] 模型不知道"八重樱是谁"

如果四条都成立：**你的系统已经具备"生命结构"了**。

---

## 致谢

感谢所有相信 AI 可以拥有"灵魂"的人。

---

*"这句话…很久以前，也有一个人对我说过。"*
