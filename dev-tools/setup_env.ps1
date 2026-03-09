# Sakura 开发环境自动设置脚本 (简化版)

param(
    [string]$PythonVersion = "3.9",
    [switch]$ForceRecreate,
    [switch]$SkipMySQL,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-Host "Sakura 开发环境自动设置脚本" -ForegroundColor Cyan
    Write-Host "用法: .\setup_env.ps1 [-PythonVersion 3.9] [-ForceRecreate] [-SkipMySQL] [-Help]" -ForegroundColor White
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-Prerequisites {
    Write-Host "`n=== 检查系统环境 ===" -ForegroundColor Cyan
    
    $allGood = $true
    
    if (Test-Command "python") {
        $pythonVersion = python --version 2>&1
        Write-Host "[✓] Python: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "[✗] Python 未安装" -ForegroundColor Red
        $allGood = $false
    }
    
    if (Test-Command "node") {
        $nodeVersion = node --version
        Write-Host "[✓] Node.js: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "[✗] Node.js 未安装" -ForegroundColor Red
        $allGood = $false
    }
    
    if (Test-Command "conda") {
        $condaVersion = conda --version 2>&1
        Write-Host "[✓] Conda: $condaVersion" -ForegroundColor Green
    } else {
        Write-Host "[!] Conda 未安装，将使用系统 Python" -ForegroundColor Yellow
    }
    
    return $allGood
}

function New-VirtualEnvironment {
    Write-Host "`n=== 设置 Python 虚拟环境 ===" -ForegroundColor Cyan
    
    if (-not (Test-Command "conda")) {
        Write-Host "跳过虚拟环境创建 (Conda 未安装)" -ForegroundColor Yellow
        return $true
    }
    
    $envName = "sakura"
    
    try {
        $existingEnv = conda env list | Select-String $envName
        if ($existingEnv -and -not $ForceRecreate) {
            Write-Host "[✓] Conda 环境 '$envName' 已存在" -ForegroundColor Green
            return $true
        }
        
        if ($existingEnv -and $ForceRecreate) {
            Write-Host "删除现有环境..." -ForegroundColor Yellow
            conda env remove -n $envName -y
        }
        
        Write-Host "创建 Conda 环境 (Python $PythonVersion)..." -ForegroundColor Yellow
        conda create -n $envName python=$PythonVersion -y
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] Conda 环境创建成功" -ForegroundColor Green
            Write-Host "激活命令: conda activate $envName" -ForegroundColor Cyan
            return $true
        } else {
            Write-Host "[✗] Conda 环境创建失败" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "[!] Conda 操作失败: $_" -ForegroundColor Red
        return $false
    }
}

function Install-PythonDependencies {
    Write-Host "`n=== 安装 Python 依赖 ===" -ForegroundColor Cyan
    
    if (-not (Test-Path "backend\requirements.txt")) {
        Write-Host "[✗] 未找到 backend/requirements.txt" -ForegroundColor Red
        return $false
    }
    
    $condaEnv = $env:CONDA_DEFAULT_ENV
    if ($condaEnv -ne "sakura" -and (Test-Command "conda")) {
        Write-Host "请先激活 sakura 环境: conda activate sakura" -ForegroundColor Yellow
        return $false
    }
    
    try {
        Write-Host "升级 pip..." -ForegroundColor Yellow
        python -m pip install --upgrade pip
        
        Write-Host "安装后端依赖..." -ForegroundColor Yellow
        Set-Location "backend"
        pip install -r requirements.txt
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] Python 依赖安装成功" -ForegroundColor Green
            Set-Location ".."
            return $true
        } else {
            Write-Host "[✗] Python 依赖安装失败" -ForegroundColor Red
            Set-Location ".."
            return $false
        }
    } catch {
        Write-Host "[!] 安装失败: $_" -ForegroundColor Red
        Set-Location ".."
        return $false
    }
}

function Install-FrontendDependencies {
    Write-Host "`n=== 安装前端依赖 ===" -ForegroundColor Cyan
    
    if (-not (Test-Path "frontend\package.json")) {
        Write-Host "[✗] 未找到 frontend/package.json" -ForegroundColor Red
        return $false
    }
    
    try {
        Write-Host "安装 Node.js 依赖..." -ForegroundColor Yellow
        Set-Location "frontend"
        npm install
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] 前端依赖安装成功" -ForegroundColor Green
            Set-Location ".."
            return $true
        } else {
            Write-Host "[✗] 前端依赖安装失败" -ForegroundColor Red
            Set-Location ".."
            return $false
        }
    } catch {
        Write-Host "[!] 安装失败: $_" -ForegroundColor Red
        Set-Location ".."
        return $false
    }
}

function Initialize-Database {
    if ($SkipMySQL) {
        Write-Host "`n=== 跳过数据库设置 ===" -ForegroundColor Yellow
        return $true
    }
    
    Write-Host "`n=== 初始化 MySQL 数据库 ===" -ForegroundColor Cyan
    
    $configPath = "backend\src\config.py"
    if (-not (Test-Path $configPath)) {
        Write-Host "[✗] 未找到配置文件: $configPath" -ForegroundColor Red
        return $false
    }
    
    Write-Host "请手动创建数据库 sakura_db:" -ForegroundColor Yellow
    Write-Host "CREATE DATABASE sakura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" -ForegroundColor White
    
    if (Test-Path "backend\src\init_db.py") {
        Write-Host "是否运行数据库初始化脚本? (y/n)" -ForegroundColor Cyan
        $choice = Read-Host
        if ($choice -eq "y") {
            Set-Location "backend\src"
            python init_db.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[✓] 数据库表初始化成功" -ForegroundColor Green
                Set-Location "..\..\"
                return $true
            } else {
                Write-Host "[✗] 数据库表初始化失败" -ForegroundColor Red
                Set-Location "..\..\"
                return $false
            }
        }
    }
    
    Set-Location "..\"
    return $true
}

function New-ConfigurationTemplate {
    Write-Host "`n=== 创建配置模板 ===" -ForegroundColor Cyan
    
    $configPath = "backend\src\config.py"
    $templatePath = "backend\src\config.example.py"
    
    if (-not (Test-Path $configPath) -and (Test-Path $templatePath)) {
        Write-Host "复制配置模板..." -ForegroundColor Yellow
        Copy-Item $templatePath $configPath
        Write-Host "[✓] 已创建 config.py，请编辑配置文件" -ForegroundColor Green
        Write-Host "需要配置:" -ForegroundColor Yellow
        Write-Host "• DATABASE_URL: MySQL 数据库连接" -ForegroundColor White
        Write-Host "• LLM_API_KEY: DeepSeek API 密钥" -ForegroundColor White
        Write-Host "• EMBEDDING_API_KEY: Embedding API 密钥" -ForegroundColor White
    } elseif (Test-Path $configPath) {
        Write-Host "[✓] 配置文件已存在" -ForegroundColor Green
    } else {
        Write-Host "[!] 未找到配置模板" -ForegroundColor Yellow
    }
}

function Main {
    Write-Host "`n🌸 Sakura 开发环境自动设置" -ForegroundColor Magenta
    Write-Host "================================" -ForegroundColor Magenta
    
    if ($Help) {
        Show-Help
        return
    }
    
    if (-not (Test-Prerequisites)) {
        Write-Host "`n请先安装缺失的依赖后再运行此脚本" -ForegroundColor Red
        return
    }
    
    $steps = @(
        { New-VirtualEnvironment },
        { Install-PythonDependencies },
        { Install-FrontendDependencies },
        { Initialize-Database },
        { New-ConfigurationTemplate }
    )
    
    $success = $true
    foreach ($step in $steps) {
        if (-not (& $step)) {
            $success = $false
            break
        }
    }
    
    Write-Host "`n=== 设置完成 ===" -ForegroundColor Cyan
    
    if ($success) {
        Write-Host "🎉 Sakura 开发环境设置成功!" -ForegroundColor Green
        Write-Host "`n下一步:" -ForegroundColor Cyan
        Write-Host "1. 编辑 backend/src/config.py 配置 API 密钥" -ForegroundColor White
        Write-Host "2. 激活虚拟环境: conda activate sakura" -ForegroundColor White
        Write-Host "3. 运行 .\start.ps1 启动开发环境" -ForegroundColor White
    } else {
        Write-Host "❌ 设置过程中遇到错误" -ForegroundColor Red
        Write-Host "`n请检查系统依赖和网络连接" -ForegroundColor Yellow
    }
}

Main
