# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

## 📚 文档

- [项目结构文档](docs/sakura/project.md) - 详细的模块和文件说明
- [开发文档](docs/sakura/开发文档.md) - 开发指南和设计原则
- [Sakura 人格设定](docs/sakura/sakura.md) - 八重樱的人格和背景

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
  └─ DB (持久化)                ← 存在的证明
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

### 🚧 Phase 1: 对话系统
- [x] 人格系统 (八重樱)
- [x] 短期记忆 (数据库持久化)
- [x] 长期记忆 (数据库持久化)
- [x] LLM 适配器 (DeepSeek / Ollama)
- [x] 用户状态追踪
- [x] Web 前端界面 (Vue 3 + Element Plus)
- [ ] 情绪状态系统完善
- [ ] 记忆检索优化

### 📋 Phase 2: 记忆系统
- [ ] 关系亲密度
- [ ] 主动回忆机制
- [ ] 重要事件提取

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

### 环境要求

- Python 3.9+
- Conda (推荐) 或 pip
- MySQL 5.7+ (数据库)

### 安装

#### 1. 配置MySQL数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

数据库配置信息（可在 `backend/src/config.py` 中修改）：
- 主机: localhost
- 端口: 3306
- 数据库名: sakura_db

#### 2. 安装Python环境

```bash
# 创建环境
conda env create -f backend/environment.yml
conda activate Sakura

# 或更新现有环境
conda env update -f backend/environment.yml --prune
```

数据库表会在首次运行时自动创建。

### 运行项目

#### 方式一：一键启动 (推荐)

直接运行根目录下的 `run.bat` 脚本即可同时启动前后端。

```bash
.\run.bat
```

#### 方式二：手动启动

**后端**
```bash
cd backend\src
# 激活环境
conda activate Sakura
# 启动服务
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端**
```bash
cd frontend
npm install  # 初次运行需要安装依赖
npm run dev
```
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 在另一个终端运行测试
cd backend
python test\test_chat.py
```

### 测试对话

访问 `http://localhost:8000/docs` 使用 Swagger UI 测试

或使用 curl：

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"依洛沐\",\"message\":\"你好，八重樱\"}"
```

---

## 项目结构

详细的项目结构请查看 [项目结构文档](docs/sakura/project.md)

```
樱/
├── backend/           # 后端服务 (FastAPI + MySQL)
│   ├── src/
│   │   ├── api/       # API 层 - 世界入口
│   │   ├── core/      # Core 层 - 意识中枢
│   │   ├── llm/       # LLM 层 - 大脑适配器
│   │   ├── memory/    # Memory 层 - 记忆系统
│   │   ├── db/        # DB 层 - 持久化
│   │   └── main.py    # 应用入口
│   └── test/          # 测试脚本
├── frontend/          # 前端界面 (Vue 3 + Element Plus)
│   ├── src/
│   │   ├── api/       # API 接口
│   │   ├── components/# Vue 组件
│   │   ├── stores/    # 状态管理
│   │   └── views/     # 页面视图
│   └── package.json
├── docs/              # 项目文档
│   ├── sakura/        # 核心文档
│   └── write/         # 开发日志
└── README.md          # 本文件
```

---

## 技术栈

- **后端框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy (异步)
- **大模型**: DeepSeek API / Ollama (可切换)
- **HTTP 客户端**: httpx (异步)
- **前端**: Vue 3 + Element Plus
- **未来计划**: 
  - 3D: Unity
  - 2D: Live2D
  - 语音: VITS / Azure TTS
  - 向量检索: FAISS / Milvus

---

## 核心特性

### 🎭 人格系统

八重樱的人格不是写死的回复，而是通过：
- 性格维度定义（温柔、执念、沉默、坚韧）
- 背景经历塑造（巫女、守护者、五百年孤独）
- 对话风格控制（古风、简短、克制）

### 🧠 记忆系统

- **短期记忆**: 最近对话上下文（数据库持久化）
- **长期记忆**: 用户信息、偏好、重要事件（分类存储）
- **用户状态**: 亲密度、情绪、互动统计
- **主动回忆**: 根据当前对话检索相关记忆
- **记忆去重**: 避免重复存储相同信息

### 🔌 模型适配

支持多种大模型后端：
- DeepSeek API (当前使用)
- Ollama (本地)
- OpenAI API (兼容)
- 其他兼容 API

模型可以随时切换，人格保持不变。

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
| DB   | 存储 | 逻辑判断 |

### 自检清单

- [ ] API 层不引用 llm
- [ ] Core 层不引用 fastapi
- [ ] Memory 不知道模型存在
- [ ] 模型不知道"八重樱是谁"

如果四条都成立：**你的系统已经具备"生命结构"了**。


## 致谢

感谢所有相信 AI 可以拥有"灵魂"的人。

---

*"这句话…很久以前，也有一个人对我说过。"*
