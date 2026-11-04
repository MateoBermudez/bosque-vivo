param(
    [switch]$Tunnel,
    [switch]$Streamlit,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [int]$PanelPort = 8501
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Push-Location "$root\backend"
try {
    uv sync --quiet --all-extras
    uv run bosquevivo setup --api-port $ApiPort
    if ($LASTEXITCODE -ne 0) { throw "bosquevivo setup falló" }
} finally { Pop-Location }

if (-not (Test-Path "$root\web\node_modules")) {
    Write-Host "Instalando dependencias de web (npm ci)..."
    Push-Location "$root\web"
    try { npm ci } finally { Pop-Location }
}

$processes = @()

$processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\backend" `
    -FilePath "uv" -ArgumentList "run", "uvicorn", "bosquevivo.api.app:app", "--port", $ApiPort

$processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\web" `
    -FilePath "npm.cmd" -ArgumentList "run", "dev", "--", "--port", $WebPort

if ($Streamlit) {
    $processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\panel" `
        -FilePath "uv" -ArgumentList "run", "streamlit", "run", "app.py", "--server.port", $PanelPort
}

if ($Tunnel) {
    $processes += Start-Process -PassThru -NoNewWindow -FilePath "cloudflared" `
        -ArgumentList "tunnel", "--url", "http://127.0.0.1:$ApiPort"
}

Write-Host "API: http://127.0.0.1:$ApiPort  Sitio: http://localhost:$WebPort"
if ($Streamlit) { Write-Host "Panel Streamlit (en desuso): http://127.0.0.1:$PanelPort" }
Write-Host "Presione Ctrl+C para detener todo."

try {
    Wait-Process -Id ($processes | ForEach-Object { $_.Id })
}
finally {
    # npm lanza procesos hijos: taskkill /T cierra todo el árbol.
    $processes | Where-Object { -not $_.HasExited } | ForEach-Object { taskkill /PID $_.Id /T /F | Out-Null }
}
