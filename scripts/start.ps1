param(
    [switch]$Tunnel,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Push-Location "$root\backend"
try {
    uv sync --quiet
    uv run bosquevivo setup --api-port $ApiPort
    if ($LASTEXITCODE -ne 0) { throw "bosquevivo setup falló" }
} finally { Pop-Location }

Push-Location "$root\web"
try {
    if (-not (Test-Path "node_modules")) { npm ci }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build falló" }
} finally { Pop-Location }

$processes = @()

$processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\backend" `
    -FilePath "uv" -ArgumentList "run", "uvicorn", "bosquevivo.api.app:app", "--host", "127.0.0.1", "--port", $ApiPort

$processes += Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\web" `
    -FilePath "npm.cmd" -ArgumentList "run", "start", "--", "--port", $WebPort

if ($Tunnel) {
    $processes += Start-Process -PassThru -NoNewWindow -FilePath "cloudflared" `
        -ArgumentList "tunnel", "--url", "http://127.0.0.1:$WebPort"
    $processes += Start-Process -PassThru -NoNewWindow -FilePath "cloudflared" `
        -ArgumentList "tunnel", "--url", "http://127.0.0.1:$ApiPort"
    Write-Host "Túneles HTTPS: copie las URL https://...trycloudflare.com que imprime cloudflared."
    Write-Host "Sitio: ponga su URL en WEB_BASE_URL (backend\.env). API: úsela para el webhook de WhatsApp."
}

Write-Host "Modo producción. API: http://127.0.0.1:$ApiPort  Sitio: http://localhost:$WebPort"
Write-Host "Presione Ctrl+C para detener todo."

try {
    Wait-Process -Id ($processes | ForEach-Object { $_.Id })
}
finally {
    $processes | Where-Object { -not $_.HasExited } | ForEach-Object { taskkill /PID $_.Id /T /F | Out-Null }
}
