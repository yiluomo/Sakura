# Sakura Development Environment Start Script (Simple)

param(
    [switch]$StopAll,
    [switch]$Status,
    [switch]$Reset
)

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Get-ServiceStatus {
    Write-Host "`n=== Sakura Service Status ===" -ForegroundColor Cyan
    
    if (Test-Port 3306) {
        Write-Host "[OK] MySQL (Port 3306)" -ForegroundColor Green
    } else {
        Write-Host "[X] MySQL (Port 3306)" -ForegroundColor Red
    }
    
    if (Test-Port 8000) {
        Write-Host "[OK] Backend (Port 8000)" -ForegroundColor Green
    } else {
        Write-Host "[X] Backend (Port 8000)" -ForegroundColor Red
    }
    
    if (Test-Port 722) {
        Write-Host "[OK] Frontend (Port 722)" -ForegroundColor Green
    } else {
        Write-Host "[X] Frontend (Port 722)" -ForegroundColor Red
    }
}

function Stop-AllServices {
    Write-Host "`n=== Stopping All Sakura Services ===" -ForegroundColor Yellow
    
    # Stop Python backend
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*main.py*" -or $_.CommandLine -like "*main.py*"}
    if ($pythonProcesses) {
        Write-Host "Stopping Python backend..." -ForegroundColor Yellow
        $pythonProcesses | ForEach-Object { $_.Kill() }
        Write-Host "[OK] Python backend stopped" -ForegroundColor Green
    }
    
    # Stop Node.js frontend
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*electron*" -or $_.CommandLine -like "*vite*"}
    if ($nodeProcesses) {
        Write-Host "Stopping Node.js frontend..." -ForegroundColor Yellow
        $nodeProcesses | ForEach-Object { $_.Kill() }
        Write-Host "[OK] Node.js frontend stopped" -ForegroundColor Green
    }
    
    Write-Host "`nAll services stopped" -ForegroundColor Green
}

function Start-Backend {
    Write-Host "`n=== Starting Backend Service ===" -ForegroundColor Cyan
    
    if (Test-Port 8000) {
        Write-Host "[OK] Backend is already running (Port 8000)" -ForegroundColor Green
        return $true
    }
    
    # Check virtual environment
    $condaEnv = $env:CONDA_DEFAULT_ENV
    if ($condaEnv -eq "sakura") {
        Write-Host "[OK] Conda environment sakura is activated" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Please activate sakura virtual environment first" -ForegroundColor Red
        Write-Host "Run: conda activate sakura" -ForegroundColor Yellow
        return $false
    }
    
    # Check configuration file
    $configPath = "backend\src\config.py"
    if (-not (Test-Path $configPath)) {
        Write-Host "[ERROR] Configuration file not found: $configPath" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Starting backend service..." -ForegroundColor Yellow
    
    # Start backend in background
    $originalPath = Get-Location
    try {
        Set-Location "backend\src"
        
        if (Test-Path "main.py") {
            Start-Process -FilePath "python" -ArgumentList "main.py" -WindowStyle Minimized -WorkingDirectory (Get-Location)
            
            # Wait for startup
            $timeout = 30
            $timer = 0
            while ($timer -lt $timeout) {
                if (Test-Port 8000) {
                    Write-Host "[OK] Backend started successfully (Port 8000)" -ForegroundColor Green
                    return $true
                }
                Start-Sleep -Seconds 1
                $timer++
                Write-Host "." -NoNewline
            }
            
            Write-Host ""
            Write-Host "[ERROR] Backend startup timeout" -ForegroundColor Red
            return $false
        } else {
            Write-Host "[ERROR] main.py not found" -ForegroundColor Red
            return $false
        }
    } finally {
        Set-Location $originalPath
    }
}

function Start-Frontend {
    Write-Host "`n=== Starting Frontend Application ===" -ForegroundColor Cyan
    
    if (Test-Port 722) {
        Write-Host "[OK] Frontend is already running (Port 722)" -ForegroundColor Green
        return $true
    }
    
    # Check frontend directory
    if (-not (Test-Path "frontend")) {
        Write-Host "[ERROR] Frontend directory not found" -ForegroundColor Red
        return $false
    }
    
    # Check node_modules
    if (-not (Test-Path "frontend\node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        Set-Location "frontend"
        npm install
        Set-Location ".."
    }
    
    Write-Host "Starting frontend Electron application..." -ForegroundColor Yellow
    
    # Start frontend in background
    $originalPath = Get-Location
    try {
        Set-Location "frontend"
        Start-Process -FilePath "npm" -ArgumentList "run", "electron:dev" -WindowStyle Minimized
        
        # Wait for startup
        $timeout = 60
        $timer = 0
        while ($timer -lt $timeout) {
            if (Test-Port 722) {
                Write-Host "[OK] Frontend started successfully (Port 722)" -ForegroundColor Green
                return $true
            }
            Start-Sleep -Seconds 1
            $timer++
            Write-Host "." -NoNewline
        }
        
        Write-Host ""
        Write-Host "[ERROR] Frontend startup timeout" -ForegroundColor Red
        return $false
        
    } finally {
        Set-Location $originalPath
    }
}

function Main {
    Write-Host "`n🌸 Sakura Development Environment Manager" -ForegroundColor Magenta
    Write-Host "======================================" -ForegroundColor Magenta
    
    if ($Status) {
        Get-ServiceStatus
        return
    }
    
    if ($StopAll) {
        Stop-AllServices
        return
    }
    
    if ($Reset) {
        Stop-AllServices
        Write-Host "`n=== Reset Environment ===" -ForegroundColor Yellow
        
        # Clean temporary files
        Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
        
        if (Test-Path "audio_cache") {
            Remove-Item "audio_cache\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "[OK] Cleaned audio cache" -ForegroundColor Green
        }
        
        if (Test-Path "memory_store\vectors") {
            Remove-Item "memory_store\vectors\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "[OK] Cleaned vector data" -ForegroundColor Green
        }
        
        Write-Host "`nEnvironment reset completed. Run the script again to start services." -ForegroundColor Green
        return
    }
    
    # Start services sequence
    Write-Host "`n=== Starting Sakura Development Environment ===" -ForegroundColor Cyan
    
    $success = $true
    
    # Start backend
    if (-not (Start-Backend)) {
        $success = $false
    }
    
    # Start frontend
    if ($success -and -not (Start-Frontend)) {
        $success = $false
    }
    
    # Show results
    Write-Host "`n=== Startup Results ===" -ForegroundColor Cyan
    
    if ($success) {
        Write-Host "🎉 Sakura development environment started successfully!" -ForegroundColor Green
        Write-Host "`nAccess URLs:" -ForegroundColor Cyan
        Write-Host "• Desktop Application: Electron window will open automatically" -ForegroundColor White
        Write-Host "• Web Interface: http://localhost:722" -ForegroundColor White
        Write-Host "• API Documentation: http://localhost:8000/docs" -ForegroundColor White
        Write-Host "`nManagement Commands:" -ForegroundColor Cyan
        Write-Host "• Check Status: .\start.ps1 -Status" -ForegroundColor White
        Write-Host "• Stop Services: .\start.ps1 -Stop" -ForegroundColor White
        Write-Host "• Reset Environment: .\start.ps1 -Reset" -ForegroundColor White
    } else {
        Write-Host "❌ Startup encountered errors" -ForegroundColor Red
        Write-Host "`nPlease check:" -ForegroundColor Yellow
        Write-Host "• MySQL service is running properly" -ForegroundColor White
        Write-Host "• sakura virtual environment is activated" -ForegroundColor White
        Write-Host "• Configuration file backend/src/config.py is correct" -ForegroundColor White
        Write-Host "• Ports 3306, 8000, 722 are available" -ForegroundColor White
    }
}

Main
