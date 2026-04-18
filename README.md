# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

---

## 🚀 快速启动

### 方式一：Docker 部署（推荐，仅后端）

此方式仅启动后端 API 服务。脚本会自动在宿主 MySQL 中创建 `sakura_db` 数据库、所有必要的数据表及初始化默认数据。

1. **环境准备**：
   - 安装 Docker 和 Docker Desktop。
   - 确保宿主机 MySQL 8.0+ 正在运行（默认 `localhost:3306`）。

2. **启动后端**：
   ```bash
   docker compose up -d --build
   ```

3. **查看启动日志**（确认数据库自动设置完成）：
   ```bash
   docker compose logs -f backend
   ```

4. **启动前端**（见下方“前端启动”部分）。

### 方式二：原生运行

1. **创建环境**：
   ```bash
   conda create -n sakura python=3.9 -y
   conda activate sakura
   ```

2. **安装后端依赖**：
   ```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   cd backend
   uv venv
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

---

## 🎨 前端启动 (Electron)

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
   npm run dev            # 浏览器模式 (http://localhost:722)
   ```

---

## 📚 文档

- [项目结构](docs/sakura/project.md)
- [开发文档](docs/sakura/开发文档.md)
- [人物设定](docs/sakura/sakura.md)
- [长期记忆使用说明](docs/sakura/长期记忆使用说明.md)

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

### 技术栈

- **后端**: FastAPI, SQLAlchemy, MySQL, FAISS (向量检索)
- **前端**: Vue 3, TypeScript, Vite, Pinia, Electron
- **AI**: DeepSeek/Ollama (LLM), BAAI/bge-small-zh-v1.5 (Embedding), GPT-SoVITS (TTS)

---

## 验证部署

> ▶️ 所有 API 接口均需携带 `X-API-Token` 请求头（见 `backend/src/config.py`）。

```bash
# 测试对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Token: sakura-private-token-a7f3k9z2m1p8q4w6" \
  -d '{"user_id": "test", "message": "你好"}'
```
