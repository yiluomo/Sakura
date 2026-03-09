# 🛠️ Sakura 开发工具集

这个目录包含了 Sakura 项目的所有开发管理工具。

## 🚀 快速开始

### 第一次设置
```powershell
# 在项目根目录运行
.\setup.ps1
```

### 日常开发
```powershell
# 启动开发环境
.\start.ps1

# 查看服务状态
.\start.ps1 -Status

# 停止所有服务
.\start.ps1 -Stop
```

## 📁 工具文件说明

### 主要脚本

| 文件 | 功能 | 详细说明 |
|------|------|----------|
| `start_dev.ps1` | 一键启动所有服务 | 自动启动 MySQL、Qdrant、后端、前端 |
| `setup_env.ps1` | 环境自动设置 | 创建虚拟环境、安装依赖、初始化数据库 |
| `check_env.ps1` | 环境隔离检查 | 确保数据库和虚拟环境不与其他项目冲突 |

### 配置和文档

| 文件 | 功能 | 说明 |
|------|------|------|
| `DEV_README.md` | 完整开发指南 | 详细的使用说明和故障排除 |
| `config.example.py` | 配置模板 | 后端配置文件的详细说明 |

## 🎯 使用场景

### 新手开发者
1. 运行 `.\setup.ps1` 自动设置环境
2. 编辑 `backend/src/config.py` 配置 API 密钥
3. 运行 `.\start.ps1` 启动开发环境

### 日常开发
1. `.\start.ps1` 启动所有服务
2. 在浏览器中访问 http://localhost:722
3. 完成开发后 `.\start.ps1 -Stop` 停止服务

### 环境检查
1. `.\check.ps1` 快速检查环境隔离
2. `.\check.ps1 -Detail` 查看详细报告
3. `.\check.ps1 -Fix` 自动修复环境问题

### 故障排除
1. `.\start.ps1 -Status` 查看服务状态
2. 查看脚本输出的错误信息
3. 参考 `DEV_README.md` 中的故障排除指南

## 🔧 高级功能

### start_dev.ps1 参数
```powershell
# 跳过环境检测（快速启动）
.\start_dev.ps1 -SkipChecks

# 重置环境（清理缓存）
.\start_dev.ps1 -Reset
```

### setup_env.ps1 参数
```powershell
# 指定 Python 版本
.\setup_env.ps1 -PythonVersion 3.10

# 强制重新创建环境
.\setup_env.ps1 -ForceRecreate

# 跳过数据库设置
.\setup_env.ps1 -SkipMySQL
```

## 📞 获取帮助

- 查看完整指南：`DEV_README.md`
- 脚本帮助：`.\setup_env.ps1 -Help`
- 项目文档：`../README.md`

---

**提示：** 通常情况下，你只需要在项目根目录使用 `.\start.ps1` 和 `.\setup.ps1` 即可，无需直接操作这个目录中的文件。
