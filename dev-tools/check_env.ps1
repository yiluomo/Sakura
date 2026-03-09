# Sakura 环境隔离检查脚本
# 确保数据库和虚拟环境与其他项目不冲突

param(
    [switch]$Fix,
    [switch]$Detail
)

$ErrorActionPreference = "Stop"

# 颜色输出
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 检查虚拟环境
function Test-VirtualEnvironment {
    Write-ColorOutput "`n=== 虚拟环境检查 ===" "Cyan"
    
    $currentEnv = $env:CONDA_DEFAULT_ENV
    $pythonPath = python -c "import sys; print(sys.executable)" 2>$null
    
    Write-ColorOutput "当前 Conda 环境: $currentEnv" "White"
    Write-ColorOutput "Python 路径: $pythonPath" "White"
    
    # 检查是否在 sakura 环境中
    if ($currentEnv -eq "sakura") {
        Write-ColorOutput "[✓] 正在使用 Sakura 专用虚拟环境" "Green"
        return $true
    } else {
        Write-ColorOutput "[!] 未使用 Sakura 专用虚拟环境" "Yellow"
        
        if ($currentEnv) {
            Write-ColorOutput "当前环境: $currentEnv" "Yellow"
            Write-ColorOutput "建议切换到 sakura 环境: conda activate sakura" "Yellow"
        } else {
            Write-ColorOutput "未激活任何 Conda 环境" "Yellow"
            Write-ColorOutput "建议创建并激活 sakura 环境: conda activate sakura" "Yellow"
        }
        
        return $false
    }
}

# 检查数据库配置
function Test-DatabaseConfig {
    Write-ColorOutput "`n=== 数据库配置检查 ===" "Cyan"
    
    $configPath = "backend\src\config.py"
    
    if (-not (Test-Path $configPath)) {
        Write-ColorOutput "[✗] 未找到配置文件: $configPath" "Red"
        return $false
    }
    
    # 读取配置文件
    $configContent = Get-Content $configPath -Raw
    
    # 提取数据库 URL
    if ($configContent -match 'DATABASE_URL\s*=\s*"([^"]+)"') {
        $dbUrl = $matches[1]
        Write-ColorOutput "数据库连接: $dbUrl" "White"
        
        # 解析数据库信息
        if ($dbUrl -match 'mysql\+aiomysql://([^@]+)@([^:]+):(\d+)/([^?]+)') {
            $user = $matches[1]
            $host = $matches[2]
            $port = $matches[3]
            $database = $matches[4]
            
            Write-ColorOutput "数据库主机: $host:$port" "White"
            Write-ColorOutput "数据库名称: $database" "White"
            Write-ColorOutput "用户名: $user" "White"
            
            # 检查数据库名称是否为 sakura_db
            if ($database -eq "sakura_db") {
                Write-ColorOutput "[✓] 使用 Sakura 专用数据库" "Green"
                return $true
            } else {
                Write-ColorOutput "[!] 数据库名称不是 sakura_db: $database" "Yellow"
                Write-ColorOutput "这可能与其他项目产生冲突" "Yellow"
                return $false
            }
        } else {
            Write-ColorOutput "[!] 无法解析数据库连接字符串" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "[!] 未找到 DATABASE_URL 配置" "Red"
        return $false
    }
}

# 检查数据库连接
function Test-DatabaseConnection {
    Write-ColorOutput "`n=== 数据库连接测试 ===" "Cyan"
    
    # 尝试连接数据库
    try {
        $result = mysql -u root -p -e "SELECT 1;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[✓] MySQL 服务连接正常" "Green"
            
            # 检查 sakura_db 是否存在
            $dbCheck = mysql -u root -p -e "SHOW DATABASES LIKE 'sakura_db';" 2>$null
            if ($dbCheck -match "sakura_db") {
                Write-ColorOutput "[✓] sakura_db 数据库存在" "Green"
                return $true
            } else {
                Write-ColorOutput "[!] sakura_db 数据库不存在" "Yellow"
                Write-ColorOutput "将创建新数据库" "Yellow"
                return $true
            }
        } else {
            Write-ColorOutput "[✗] MySQL 连接失败" "Red"
            Write-ColorOutput "请检查 MySQL 服务是否运行" "Yellow"
            return $false
        }
    } catch {
        Write-ColorOutput "[!] 无法测试 MySQL 连接" "Yellow"
        Write-ColorOutput "请确保 MySQL 客户端已安装" "Yellow"
        return $false
    }
}

# 检查端口冲突
function Test-PortConflicts {
    Write-ColorOutput "`n=== 端口冲突检查 ===" "Cyan"
    
    $ports = @{
        3306 = "MySQL"
        6333 = "Qdrant"
        8000 = "Backend"
        722 = "Frontend"
    }
    
    $conflicts = @()
    
    foreach ($port in $ports.Keys) {
        $service = $ports[$port]
        
        # 检查端口是否被占用
        $connection = New-Object System.Net.Sockets.TcpClient
        try {
            $connection.Connect("localhost", $port)
            $connection.Close()
            
            # 检查占用进程
            $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($process) {
                $processName = Get-Process -Id $process.OwningProcess -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName
                Write-ColorOutput "[!] 端口 $port ($service) 被占用 - 进程: $processName" "Yellow"
                $conflicts += @{ Port = $port; Service = $service; Process = $processName }
            } else {
                Write-ColorOutput "[!] 端口 $port ($service) 被占用" "Yellow"
                $conflicts += @{ Port = $port; Service = $service; Process = "Unknown" }
            }
        } catch {
            Write-ColorOutput "[✓] 端口 $port ($service) 可用" "Green"
        }
    }
    
    return $conflicts.Count -eq 0
}

# 检查文件路径冲突
function Test-PathConflicts {
    Write-ColorOutput "`n=== 文件路径检查 ===" "Cyan"
    
    $paths = @{
        "memory_store" = "长期记忆存储"
        "audio_cache" = "音频缓存"
        "qdrant_storage" = "向量数据存储"
        "memory_exports" = "记忆导出"
    }
    
    $conflicts = @()
    
    foreach ($path in $paths.Keys) {
        $description = $paths[$path]
        $fullPath = Join-Path $PWD $path
        
        if (Test-Path $fullPath) {
            $files = Get-ChildItem $fullPath -Recurse -ErrorAction SilentlyContinue | Measure-Object
            Write-ColorOutput "[✓] $description 目录存在: $path ($($files.Count) 个文件)" "Green"
        } else {
            Write-ColorOutput "[!] $description 目录不存在: $path" "Yellow"
            Write-ColorOutput "启动时会自动创建" "Yellow"
        }
    }
    
    return $true
}

# 生成环境报告
function New-EnvironmentReport {
    Write-ColorOutput "`n=== 环境隔离报告 ===" "Magenta"
    
    $report = @{
        VirtualEnv = Test-VirtualEnvironment
        Database = Test-DatabaseConfig
        Connection = Test-DatabaseConnection
        Ports = Test-PortConflicts
        Paths = Test-PathConflicts
    }
    
    Write-ColorOutput "`n检查结果总结:" "Cyan"
    
    foreach ($item in $report.Keys) {
        $status = if ($report[$item]) { "[✓]" } else { "[!]" }
        $color = if ($report[$item]) { "Green" } else { "Yellow" }
        
        switch ($item) {
            "VirtualEnv" { Write-ColorOutput "$status 虚拟环境隔离" $color }
            "Database" { Write-ColorOutput "$status 数据库配置" $color }
            "Connection" { Write-ColorOutput "$status 数据库连接" $color }
            "Ports" { Write-ColorOutput "$status 端口冲突" $color }
            "Paths" { Write-ColorOutput "$status 文件路径" $color }
        }
    }
    
    $allGood = $report.Values -contains $true -and $report.Values -notcontains $false
    
    if ($allGood) {
        Write-ColorOutput "`n🎉 环境隔离检查通过！" "Green"
        Write-ColorOutput "Sakura 项目完全独立，不会与其他项目冲突。" "Green"
    } else {
        Write-ColorOutput "`n⚠️ 发现潜在的环境冲突" "Yellow"
        Write-ColorOutput "建议运行以下命令修复:" "Yellow"
        Write-ColorOutput ".\check_env.ps1 -Fix" "White"
    }
    
    return $allGood
}

# 自动修复环境问题
function Repair-Environment {
    Write-ColorOutput "`n=== 自动修复环境问题 ===" "Yellow"
    
    # 1. 检查并创建 sakura 虚拟环境
    $currentEnv = $env:CONDA_DEFAULT_ENV
    if ($currentEnv -ne "sakura") {
        Write-ColorOutput "检查 sakura 虚拟环境..." "Yellow"
        
        try {
            $envExists = conda env list | Select-String "sakura"
            if (-not $envExists) {
                Write-ColorOutput "创建 sakura 虚拟环境..." "Yellow"
                conda create -n sakura python=3.9 -y
            }
            
            Write-ColorOutput "请手动激活 sakura 环境:" "Cyan"
            Write-ColorOutput "conda activate sakura" "White"
        } catch {
            Write-ColorOutput "[!] 无法自动创建虚拟环境" "Red"
        }
    }
    
    # 2. 检查数据库配置
    $configPath = "backend\src\config.py"
    if (Test-Path $configPath) {
        $configContent = Get-Content $configPath -Raw
        
        if ($configContent -match 'DATABASE_URL\s*=\s*"([^"]+)"') {
            $dbUrl = $matches[1]
            if ($dbUrl -match '/([^/?]+)(?:\?|$)') {
                $database = $matches[1]
                if ($database -ne "sakura_db") {
                    Write-ColorOutput "[!] 数据库名称不是 sakura_db: $database" "Yellow"
                    Write-ColorOutput "请手动修改配置文件中的 DATABASE_URL" "Yellow"
                    Write-ColorOutput "确保数据库名称为 sakura_db" "White"
                }
            }
        }
    }
    
    # 3. 创建必要的目录
    $dirs = @("memory_store", "audio_cache", "qdrant_storage", "memory_exports")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorOutput "[✓] 创建目录: $dir" "Green"
        }
    }
    
    Write-ColorOutput "`n修复完成，请重新运行检查:" "Cyan"
    Write-ColorOutput ".\check_env.ps1" "White"
}

# 主程序
function Main {
    Write-ColorOutput "`n🔍 Sakura 环境隔离检查器" "Magenta"
    Write-ColorOutput "================================" "Magenta"
    
    if ($Fix) {
        Repair-Environment
        return
    }
    
    if ($Detail) {
        New-EnvironmentReport
    } else {
        # 快速检查
        $quickChecks = @{
            VirtualEnv = (Test-VirtualEnvironment)
            Database = (Test-DatabaseConfig)
        }
        
        Write-ColorOutput "`n快速检查结果:" "Cyan"
        
        if ($quickChecks.VirtualEnv -and $quickChecks.Database) {
            Write-ColorOutput "🎉 环境隔离正常！" "Green"
            Write-ColorOutput "虚拟环境和数据库配置都正确。" "Green"
        } else {
            Write-ColorOutput "⚠️ 发现环境配置问题" "Yellow"
            
            if (-not $quickChecks.VirtualEnv) {
                Write-ColorOutput "• 虚拟环境配置问题" "White"
            }
            
            if (-not $quickChecks.Database) {
                Write-ColorOutput "• 数据库配置问题" "White"
            }
            
            Write-ColorOutput "`n运行详细检查:" "Cyan"
            Write-ColorOutput ".\check_env.ps1 -Detail" "White"
            Write-ColorOutput "自动修复问题:" "Cyan"
            Write-ColorOutput ".\check_env.ps1 -Fix" "White"
        }
    }
}

# 执行主程序
Main
