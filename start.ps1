# Sakura 快速启动脚本

param(
    [switch]$Stop,
    [switch]$Status
)

$scriptPath = Join-Path $PSScriptRoot "dev-tools\start_dev.ps1"

if ($Stop) {
    & $scriptPath -StopAll
} elseif ($Status) {
    & $scriptPath -Status
} else {
    & $scriptPath
}
