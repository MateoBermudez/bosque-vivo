param(
    [switch]$Tunnel,
    [int]$ApiPort = 8000,
    [int]$PanelPort = 8501
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$root\backend\.env")) {
    Copy-Item "$root\.env.example" "$root\backend\.env"
    Write-Host "Se creó backend\.env. Complete las claves y vuelva a ejecutar."
    exit 1
}

$processes = @()

$processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\backend" `
    -FilePath "uv" -ArgumentList "run", "uvicorn", "bosquevivo.api.app:app", "--port", $ApiPort

$processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\panel" `
    -FilePath "uv" -ArgumentList "run", "streamlit", "run", "app.py", "--server.port", $PanelPort

if ($Tunnel) {
    $processes += Start-Process -PassThru -NoNewWindow -FilePath "cloudflared" `
        -ArgumentList "tunnel", "--url", "http://127.0.0.1:$ApiPort"
}

Write-Host "API: http://127.0.0.1:$ApiPort  Panel: http://127.0.0.1:$PanelPort"
Write-Host "Presione Ctrl+C para detener todo."

try {
    Wait-Process -Id ($processes | ForEach-Object { $_.Id })
}
finally {
    $processes | Where-Object { -not $_.HasExited } | Stop-Process -Force
}
