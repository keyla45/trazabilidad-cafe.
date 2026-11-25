# Ejecutar desde la carpeta del proyecto CafeTrace en PowerShell.
$ErrorActionPreference = 'Stop'
$nombre = 'CafeTrace_UPEC_5_Areas_Experiencia_2026.zip'
$zip = Get-ChildItem -Path $env:USERPROFILE -Filter $nombre -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $zip) { Write-Host 'Primero descarga el ZIP de ChatGPT en tu computadora.' -ForegroundColor Yellow; exit 1 }
if (-not (Test-Path '.\manage.py')) { Write-Host 'Abre la terminal dentro de la carpeta CafeTrace que contiene manage.py.' -ForegroundColor Red; exit 1 }
$backup = Join-Path (Get-Location) ('respaldo_visual_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup | Out-Null
Copy-Item '.\templates' (Join-Path $backup 'templates') -Recurse
Copy-Item '.\static' (Join-Path $backup 'static') -Recurse
if (Test-Path '.\db.sqlite3') { Copy-Item '.\db.sqlite3' (Join-Path $backup 'db.sqlite3') }
$temp = Join-Path $env:TEMP 'cafetrace_5_areas_experiencia'
New-Item -ItemType Directory -Path $temp -Force | Out-Null
Expand-Archive -LiteralPath $zip.FullName -DestinationPath $temp -Force
$origen = Join-Path $temp 'CafeTrace'
if (-not (Test-Path (Join-Path $origen 'templates\base.html'))) { throw 'Estructura ZIP incorrecta.' }
Copy-Item (Join-Path $origen 'templates\*') '.\templates\' -Recurse -Force
Copy-Item (Join-Path $origen 'static\*') '.\static\' -Recurse -Force
Write-Host 'Interfaz actualizada. Se conservaron models, usuarios, migraciones y base de datos.' -ForegroundColor Green
Write-Host "Respaldo: $backup"
& '.\venv\Scripts\python.exe' manage.py check
