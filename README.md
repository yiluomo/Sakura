# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

---

## 🚀 快速启动

### 1. 配置环境

项目使用环境变量来进行核心配置。在启动前后端前，请进行以下环境配置：

1. **后端配置**：
   - 在项目根目录下，复制 `.env.example` 并重命名为 `.env`：
     ```bash
     cp .env.example .env
     ```
   - 打开 `.env`，填入您的 **MySQL 数据库连接串** (`DATABASE_URL`) 和 **LLM API 密钥** 等配置。

2. **前端配置**：
   - 进入 `frontend` 目录，复制 `.env.example` 并重命名为 `.env`：
     ```bash
     cd frontend
     cp .env.example .env
     ```
   - （可选）若需自定义后端鉴权 Token，可在此修改 `VITE_API_TOKEN`，使其与后端的 `API_TOKEN` 保持一致。

### 2. 后端启动

1. **安装 uv 包管理器**（若尚未安装）：
   ```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **创建环境与安装后端依赖**：
   ```bash
   cd backend
   uv venv --python 3.14
   .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **数据库初始化**：
   ```bash
   cd src
   python setup_db.py  # 全自动创建库表、同步字段及初始化数据
   ```

4. **启动后端**：
   ```bash
   python main.py
   ```
(首次运行会自动下载模型，请耐心等待...)
---

## 🎨 前端启动 (Electron / 浏览器)

无论使用哪种方式启动后端，前端均需在本机执行：

1. **安装依赖**：
   ```bash
   cd frontend
   npm install
   ```

2. **启动应用**：
   ```bash
   npm run electron:dev   # 桌面应用模式
   # 或
   npm run dev            # 浏览器模式 (访问 http://localhost:722)
   ```

---

## 📚 文档

- [项目结构](docs/sakura/project.md)
- [开发文档](docs/sakura/开发文档.md)
- [人物设定](docs/sakura/sakura.md)
- [长期记忆使用说明](docs/sakura/长期记忆使用说明.md)

---

## 核心理念与架构

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
  ├─ Memory (记忆系统)      ← 她的过去与现在（支持 RAG 与自动归档，不存本地明文聊天记录）
  ├─ TTS (语音合成)         ← 她的声音
  └─ DB + 文件 (持久化)     ← 存在的证明
```

### 🧠 隐私与记忆管理说明
- **对话隐私保护**：系统已禁用将原始聊天历史记录明文写入本地物理文件（如 `.md` 文件）的功能。所有的对话均安全地记录在您的本地 MySQL 数据库中。
- **记忆与向量召回**：系统会自动归档旧对话。提取的“记忆摘要/关键词”会同步存入数据库中，并生成 FAISS 向量索引以支持长期召回。
- **数据迁移备份**：内置记忆的**导入与导出功能**，支持一键备份和恢复您的所有对话历史和长期记忆（基于 JSON 格式，在前端页面一键操作即可完成迁移）。

### 技术栈

- **后端**: FastAPI, SQLAlchemy, MySQL, FAISS (向量检索)
- **前端**: Vue 3, TypeScript, Vite, Pinia, Electron
- **AI**: DeepSeek/Ollama (LLM), BAAI/bge-small-zh-v1.5 (Embedding), GPT-SoVITS (TTS)

---

## 验证部署

> ▶️ 所有 API 接口均需携带 `X-API-Token` 请求头（在 `.env` 中通过 `API_TOKEN` 自定义）。

```bash
# 测试对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Token: sakura-private-token-a7f3k9z2m1p8q4w6" \
  -d '{"user_id": "test", "message": "你好"}'
```
