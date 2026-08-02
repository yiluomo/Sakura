# 樱 - Sakura

> *"外面的世界，已过了五百年。这里…至少还有熟悉的风景。"*

一个致力于构建真实"存在"的对话生命系统。

---

## 🗄️ 第一步：选择数据库

> 启动前先做这个选择：它决定后端安装哪个数据库驱动、数据存在哪里。切换只需改 `.env` 后重跑启动脚本。

| 模式 | 适用场景 | 安装命令 | 说明 |
|---|---|---|---|
| **SQLite**（默认） | 体验、开发、单机轻量 | `uv sync --extra sqlite` | 零配置，无需安装数据库；数据文件在 `backend/src/db/data/sakura.db` |
| **MySQL** | 正式使用、多设备、完整数据管理 | `uv sync --extra mysql` | 需先安装并启动 MySQL，手动创建数据库 |

两种模式**互斥**：选 MySQL 不会安装 aiosqlite（SQLite 驱动），选 SQLite 也不会安装 MySQL 驱动，避免多余下载。

**使用 SQLite**：什么都不用改，直接进入下方的快速开始。

**使用 MySQL：**

```sql
CREATE DATABASE sakura_db CHARACTER SET utf8mb4;
```

```env
# 根目录 .env
DATABASE_URL=mysql+aiomysql://<用户名>:<密码>@localhost:3306/sakura_db
```

切换数据库模式后，重新执行对应的 `uv sync --extra <模式>` 并运行 `python setup_db.py` 初始化（一键脚本会自动处理）。

## ✨ 功能特性

- **分层生命架构**：表现层（Electron / 语音）→ API 层（FastAPI）→ Core 层（人格/决策/调度）→ 子系统层（LLM / Memory / TTS / DB）
- **多 LLM 适配**：DeepSeek / Qwen / 豆包 / OpenAI / 自定义 API
- **RAG 长期记忆**：本地 Embedding + FAISS 向量检索，自动归档旧对话
- **记忆管理**：记忆摘要/关键词入库，支持一键导入导出与迁移
- **语音合成**：GPT-SoVITS（可选）
- **隐私优先**：对话默认保存在本地数据库，不落明文聊天文件；静态 Token 鉴权

## 🧱 技术栈

- **后端**：FastAPI、SQLAlchemy、MySQL / SQLite、FAISS、sentence-transformers
- **前端**：Vue 3、TypeScript、Vite、Pinia、Electron
- **AI**：DeepSeek/Qwen/豆包/OpenAI（LLM）、BAAI/bge-small-zh-v1.5（Embedding）、GPT-SoVITS（TTS）

---

## 🚀 快速开始

> 开始前请先完成上方的「第一步：选择数据库」——一键脚本会自动读取 `.env` 判断数据库模式。

### 方式一：一键脚本（推荐）

Windows（PowerShell）：

```powershell
.\start.bat              # 桌面应用模式
.\start.ps1 -Mode Browser  # 浏览器模式（http://localhost:722）
```

脚本会自动完成：生成缺失的 `.env` → 按数据库模式安装后端依赖 → 前端 `node_modules` 缺失时自动 `npm install` → 隐藏启动后端（日志写入 `.logs/`）→ 前端就绪后再启动。

常用命令：

```powershell
.\start.ps1 -InitDB      # 初始化/同步数据库后启动
.\start.ps1 -Stop        # 停止后端
.\start.ps1 -Logs        # 打开日志目录
.\start.ps1 -CleanLogs   # 清空历史日志
```

### 方式二：手动启动

前置条件：Node.js 18+；如选择 MySQL，还需安装 MySQL。后端使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境：

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **首次运行提示**：`uv sync` 会下载 torch、sentence-transformers 等依赖（约 2-4 GB），后端首次启动还会自动下载 Embedding 模型（约 95MB）。请耐心等待，一键脚本最多等待 5 分钟。

**1. 配置环境**

```powershell
copy .env.example .env               # 项目根目录
copy frontend\.env.example frontend\.env
```

编辑根目录 `.env`：按下方[数据库选择](#-数据库选择)配置 `DATABASE_URL`，并填入 LLM API Key。

**2. 启动后端**

```powershell
cd backend
uv sync --extra sqlite               # SQLite 模式（零配置）
# 或 uv sync --extra mysql           # MySQL 模式

cd src
python setup_db.py                   # 首次运行：初始化数据库
python main.py                       # 启动后端（http://localhost:8000）
```

> 首次启动会自动下载 Embedding 模型（约 95MB），请耐心等待。

**3. 启动前端**

```powershell
cd frontend
npm install
npm run electron:dev                 # 桌面应用模式
# 或 npm run dev                     # 浏览器模式（http://localhost:722）
```

---

## ⚙️ 配置说明

根目录 `.env` 关键项（完整模板见 `.env.example`）：

| 配置 | 说明 |
|---|---|
| `DATABASE_URL` | 数据库连接串；不设置时默认使用 SQLite |
| `LLM_PROVIDER` | LLM 供应商：deepseek / qwen / doubao / openai / custom |
| `PROVIDER_*_KEY` | 各供应商 API Key |
| `LLM_API_KEY` / `LLM_MODEL` | 记忆总结等后台任务使用的模型 |
| `EMBEDDING_MODE` | `local`（默认，本地模型）或 `api` |
| `API_TOKEN` | 后端鉴权 Token，**上线前务必更换** |
| `TTS_ENABLED` | 是否启用 GPT-SoVITS 语音合成 |

前端 `frontend/.env` 中的 `VITE_API_TOKEN` 必须与后端 `API_TOKEN` 一致。

---

## ✅ 验证

所有 API 接口均需携带 `X-API-Token` 请求头：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Token: <你的 API_TOKEN>" \
  -d '{"user_id": "test", "message": "你好"}'
```

---

## 📄 日志

一键启动时，日志统一保存在项目根目录 `.logs/`：

- 后端：`backend-<时间戳>.log` / `backend-<时间戳>.err.log`
- 前端：`frontend-<时间戳>.log`

运行 `.\start.ps1 -Logs` 直接打开日志目录，`-CleanLogs` 清空历史日志。

---

## ❓ 常见问题

**1. Electron 下载慢 / 失败？**

国内镜像已内置：一键脚本会自动设置 `ELECTRON_MIRROR` 环境变量，仓库中的 `frontend/.npmrc` 也配置了 `electron_mirror`（提交到仓库后对直接执行 `npm install` 的用户生效）。若两者都没有，可手动执行：

```powershell
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"; npm install
```

**2. Embedding 模型下载慢？**

首次启动会从 HuggingFace 下载 `BAAI/bge-small-zh-v1.5`，代码默认已走 `hf-mirror.com` 镜像；也可自行设置 `HF_ENDPOINT`。

**3. 提示找不到 aiosqlite / aiomysql？**

依赖与数据库模式不匹配，运行对应的 `uv sync --extra sqlite` 或 `uv sync --extra mysql`。

**4. 后端启动失败？**

查看 `.logs/backend-*.err.log`；确认 `.env` 中 `DATABASE_URL` 与已安装依赖的模式一致；MySQL 模式确认数据库已创建。

**5. 端口被占用？**

前端固定 722、后端 8000。启动脚本检测到 8000 已被占用时会直接复用现有后端。

---

## 🧠 隐私与记忆管理

- 对话记录保存在本地数据库（SQLite 文件或 MySQL），不写入明文 `.md` 聊天记录
- 旧对话自动归档为"记忆摘要/关键词"入库，并生成 FAISS 向量索引支持长期召回
- 内置记忆导入导出功能（JSON），前端一键完成备份与迁移

## 📁 项目结构

```
.
├─ backend/               # FastAPI 后端（运行目录为 src/）
│  ├─ src/api/            # 路由：chat / memory / tts
│  ├─ src/core/           # 人格 / 对话 / 情绪
│  ├─ src/memory/         # 短期/长期记忆、向量检索
│  ├─ src/db/             # 数据模型与访问
│  ├─ pyproject.toml      # 依赖定义（uv.lock 锁定版本）
│  └─ uv.lock
├─ frontend/              # Vue 3 + Vite + Electron
├─ start.ps1 / start.bat  # 一键启动脚本（Windows）
├─ .env.example           # 后端环境配置模板
└─ README.md
```
