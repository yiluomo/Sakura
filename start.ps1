<#
.SYNOPSIS
    One-command launcher for the Sakura project (backend + frontend).

.DESCRIPTION
    - Starts the FastAPI backend (port 8000) hidden; logs go to .logs/.
    - Starts the frontend in the current console; output is also saved to .logs/.
    - Detects SQLite / MySQL mode from .env and installs the matching driver extra.

.EXAMPLE
    .\start.ps1                      # desktop app mode (default)
    .\start.ps1 -Mode Browser        # browser mode: http://localhost:722
    .\start.ps1 -InitDB              # run database setup first, then start
    .\start.ps1 -InstallDeps         # force dependency install via uv sync
    .\start.ps1 -Logs                # open the logs folder
    .\start.ps1 -CleanLogs           # delete old logs
    .\start.ps1 -Stop                # stop the backend started by this script
#>

[CmdletBinding()]
param(
    [ValidateSet("Desktop", "Browser")]
    [string]$Mode = "Desktop",
    [switch]$InitDB,
    [switch]$InstallDeps,
    [switch]$SkipInstall,
    [switch]$Stop,
    [switch]$Logs,
    [switch]$CleanLogs
)

$ErrorActionPreference = "Continue"

$Root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir  = Join-Path $Root "backend"
$BackendSrc  = Join-Path $BackendDir "src"
$FrontendDir = Join-Path $Root "frontend"
$VenvPython  = Join-Path $BackendDir ".venv\Scripts\python.exe"
$LogDir      = Join-Path $Root ".logs"
$PidFile     = Join-Path $env:TEMP "sakura-backend.pid"
$ApiPort     = 8000
$WebPort     = 722

function Write-Step  { Write-Host ""; Write-Host "==> $args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "    OK: $args" -ForegroundColor Green }
function Write-Warn2 { Write-Host "    WARN: $args" -ForegroundColor Yellow }
function Write-Fail  { Write-Host "    FAIL: $args" -ForegroundColor Red }

function Test-PortListener([int]$Port) {
    try { return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) }
    catch { return $false }
}

function Test-PythonImport([string]$Module) {
    # 捕获 stderr（PS 5.1 会把原生命令 stderr 当作错误），只依据退出码判断
    $null = & $VenvPython -c "import $Module" 2>&1
    return ($LASTEXITCODE -eq 0)
}

function Get-DbMode {
    # 优先级：环境变量 > 根目录 .env 中的 DATABASE_URL > 默认 SQLite
    $url = $env:DATABASE_URL
    if (-not $url) {
        $envFile = Join-Path $Root ".env"
        if (Test-Path $envFile) {
            $line = Select-String -Path $envFile -Pattern '^\s*DATABASE_URL\s*=' | Select-Object -First 1
            if ($line) {
                $url = ($line.Line -split '=', 2)[1].Trim().Trim('"').Trim("'")
            }
        }
    }
    if (-not $url) { return "sqlite" }
    if ($url.StartsWith("sqlite")) { return "sqlite" }
    if ($url.StartsWith("mysql"))  { return "mysql" }
    return "unknown"
}

function Stop-SakuraBackend {
    Write-Step "Stopping Sakura backend..."
    $pids = New-Object 'System.Collections.Generic.List[int]'
    if (Test-Path $PidFile) {
        Get-Content $PidFile | ForEach-Object {
            if ($_ -match '^\d+$') { $pids.Add([int]$_) }
        }
    }
    Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { $pids.Add([int]$_.OwningProcess) }

    $unique = $pids | Sort-Object -Unique
    if ($unique.Count -eq 0) {
        Write-Warn2 "No running backend found on port $ApiPort."
    } else {
        foreach ($p in $unique) {
            Write-Ok "Terminating process $p and its children..."
            & taskkill.exe /PID $p /T /F 2>$null | Out-Null
        }
    }
    Remove-Item $PidFile -ErrorAction SilentlyContinue
}

if ($Stop) {
    Stop-SakuraBackend
    exit 0
}

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}
if ($Logs) {
    Invoke-Item $LogDir
    Write-Ok "Opened logs folder: $LogDir"
    exit 0
}
if ($CleanLogs) {
    $resolvedLogDir = (Resolve-Path -LiteralPath $LogDir).Path
    $resolvedRoot   = (Resolve-Path -LiteralPath $Root).Path
    if (-not $resolvedLogDir.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean outside workspace: $resolvedLogDir"
    }
    Get-ChildItem -LiteralPath $resolvedLogDir -File -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Ok "Cleaned logs folder."
    exit 0
}

$dbMode = Get-DbMode

# 判断 DATABASE_URL 是否被显式配置（环境变量或 .env），用于给出切换提示
$dbExplicit = [bool]$env:DATABASE_URL
if (-not $dbExplicit) {
    $envFile = Join-Path $Root ".env"
    if (Test-Path $envFile) {
        $dbExplicit = [bool](Select-String -Path $envFile -Pattern '^\s*DATABASE_URL\s*=' | Select-Object -First 1)
    }
}

# Database selection hint (always shown first)
Write-Host ""
Write-Host "========================================================" -ForegroundColor Yellow
Write-Host "  DATABASE MODE: $dbMode" -ForegroundColor Yellow
if ($dbMode -eq "sqlite" -and -not $dbExplicit) {
    Write-Host "  - Current: SQLite (default, zero-config). Just start." -ForegroundColor Yellow
    Write-Host "  - To use MySQL instead, edit .env and set:" -ForegroundColor Yellow
    Write-Host "      DATABASE_URL=mysql+aiomysql://<user>:<password>@localhost:3306/sakura_db" -ForegroundColor Yellow
    Write-Host "    create the database, then rerun this script." -ForegroundColor Yellow
} else {
    Write-Host "  - Mode detected from DATABASE_URL in .env." -ForegroundColor Yellow
    Write-Host "  - To switch database: edit .env, then rerun this script." -ForegroundColor Yellow
}
Write-Host "========================================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================================" -ForegroundColor Magenta
Write-Host "  Sakura Launcher" -ForegroundColor Magenta
Write-Host "  Mode     : $Mode" -ForegroundColor Magenta
Write-Host "  Database : $dbMode" -ForegroundColor Magenta
Write-Host "  Backend  : http://localhost:$ApiPort" -ForegroundColor Magenta
Write-Host "  Frontend : http://localhost:$WebPort  (browser mode)" -ForegroundColor Magenta
Write-Host "  Logs     : $LogDir" -ForegroundColor Magenta
Write-Host "========================================================" -ForegroundColor Magenta

# ---- .env files ------------------------------------------------------
if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Warn2 "Created .env from .env.example - check DATABASE_URL / API keys."
}
if (-not (Test-Path (Join-Path $FrontendDir ".env"))) {
    Copy-Item (Join-Path $FrontendDir ".env.example") (Join-Path $FrontendDir ".env")
    Write-Warn2 "Created frontend/.env from .env.example."
}

# ---- backend environment ---------------------------------------------
Write-Step "Checking backend environment (database mode: $dbMode)..."
$freshVenv = $false
if (-not (Test-Path $VenvPython)) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Fail "uv not found. Install it first:"
        Write-Fail "  powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
        exit 1
    }
    Write-Ok "Creating backend virtualenv (Python 3.14)..."
    & uv venv --python 3.14 (Join-Path $BackendDir ".venv")
    $freshVenv = $true
}

if ($dbMode -eq "unknown") {
    Write-Warn2 "DATABASE_URL in .env is neither sqlite nor mysql - using default SQLite for dependency install."
    $dbMode = "sqlite"
}

if (-not $SkipInstall) {
    # 检测对应驱动是否已安装；缺失时自动补装（首次安装可能耗时较长）
    $probeModule = "aiosqlite"
    if ($dbMode -ne "sqlite") { $probeModule = "aiomysql" }
    $needInstall = $InstallDeps
    if (-not $needInstall) {
        $needInstall = -not (Test-PythonImport $probeModule)
    }
    if ($needInstall) {
        Write-Ok "Installing backend dependencies (uv sync --extra $dbMode, first run may take several minutes)..."
        Push-Location $BackendDir
        & uv sync --extra $dbMode
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -ne 0) {
            Write-Fail "uv sync failed (exit code $code)."
            exit 1
        }
    } else {
        Write-Ok "$probeModule already available, skipping install."
    }
} else {
    Write-Ok "Dependency install skipped (-SkipInstall)."
}

# ---- frontend deps ---------------------------------------------------
Write-Step "Checking frontend dependencies..."
# Electron 镜像：优先用环境变量（.npmrc 的 electron_mirror 键在新版 npm 会废弃）
if (-not $env:ELECTRON_MIRROR) {
    $env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
}
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    if ($SkipInstall) {
        Write-Fail "frontend/node_modules is missing and install was skipped."
        exit 1
    }
    Write-Ok "Running npm install (first run, may take a while)..."
    Push-Location $FrontendDir
    & npm.cmd install 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) {
        Write-Fail "npm install failed (exit code $code)."
        exit 1
    }
} else {
    Write-Ok "node_modules found, skipping npm install."
}

# ---- database init ---------------------------------------------------
if ($InitDB) {
    Write-Step "Initializing database (setup_db.py)..."
    Push-Location $BackendSrc
    & $VenvPython setup_db.py
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) {
        Write-Fail "Database setup failed. Check DATABASE_URL and (for MySQL) that the database exists."
        exit 1
    }
}

# ---- backend ---------------------------------------------------------
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outLog = Join-Path $LogDir "backend-$stamp.log"
$errLog = Join-Path $LogDir "backend-$stamp.err.log"

Write-Step "Starting backend (http://localhost:$ApiPort, logs -> $outLog)..."
if (Test-PortListener $ApiPort) {
    Write-Ok "Backend already listening on port $ApiPort - reusing it."
} else {
    $p = Start-Process -FilePath $VenvPython -ArgumentList "main.py" `
        -WorkingDirectory $BackendSrc -WindowStyle Hidden `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
    Set-Content -Path $PidFile -Value $p.Id
    Write-Ok "Backend launcher PID $($p.Id) started (hidden)."
}

Write-Step "Waiting for backend to become ready..."
Write-Ok "First run may take a few minutes (installing deps / downloading the embedding model)."
$ready = $false
for ($i = 0; $i -lt 150; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$ApiPort/" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Seconds 2
    }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
}
Write-Host ""
if (-not $ready) {
    Write-Fail "Backend did not respond at http://localhost:$ApiPort within 300s."
    Write-Fail "First run downloads the embedding model - if this is the first start, wait longer or rerun."
    Write-Fail "Check the latest log files under $LogDir"
    exit 1
}
Write-Ok "Backend is up."

# ---- frontend --------------------------------------------------------
$frontLog = Join-Path $LogDir "frontend-$stamp.log"
Write-Step "Starting frontend ($Mode mode, logs -> $frontLog)..."
Push-Location $FrontendDir
if ($Mode -eq "Desktop") {
    Write-Ok "Desktop app mode (Electron). Backend logs are under $LogDir"
    & npm.cmd run electron:dev 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $frontLog
} else {
    Write-Ok "Browser mode - open http://localhost:$WebPort"
    & npm.cmd run dev 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $frontLog
}
$frontendCode = $LASTEXITCODE
Pop-Location

Write-Step "Frontend exited (code $frontendCode)."
Write-Ok "Logs: $LogDir"
Write-Ok "Backend keeps running. Stop it with '.\start.ps1 -Stop'."
