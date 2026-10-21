param(
    [switch]$Tunnel,
    [switch]$Streamlit,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [int]$PanelPort = 8501
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$root\backend\.env")) {
    Copy-Item "$root\.env.example" "$root\backend\.env"
    Write-Host "Se creó backend\.env. Complete las claves y vuelva a ejecutar."
    exit 1
}

# El sitio (web/) se conecta a la API con el mismo ADMIN_TOKEN del backend.
# Si web\.env.local no existe, se genera a partir de backend\.env.
if (-not (Test-Path "$root\web\.env.local")) {
    $adminToken = ""
    $line = Select-String -Path "$root\backend\.env" -Pattern '^\s*ADMIN_TOKEN\s*=\s*(.*)$' | Select-Object -First 1
    if ($line) { $adminToken = $line.Matches[0].Groups[1].Value.Trim() }
    $envLines = @(
        "BV_DATA_SOURCE=live",
        "BACKEND_URL=http://127.0.0.1:$ApiPort",
        "ADMIN_TOKEN=$adminToken"
    )
    # UTF-8 sin BOM: con BOM, Next no reconocería la primera variable.
    [System.IO.File]::WriteAllLines("$root\web\.env.local", $envLines, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "Se creó web\.env.local (modo live). Define AUDITOR_ACCESS_CODE y SESSION_SECRET para proteger el área de auditores."
}

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
