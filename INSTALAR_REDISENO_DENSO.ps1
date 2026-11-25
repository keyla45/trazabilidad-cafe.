# Ejecutar desde la carpeta CafeTrace. No modifica base de datos ni venv.
$ErrorActionPreference = "Stop"
$origen = Join-Path $PSScriptRoot "CafeTrace"
if (-not (Test-Path (Join-Path $origen "templates"))) { throw "No se encuentra la carpeta CafeTrace en el paquete" }
if (Test-Path ".\db.sqlite3") { Copy-Item ".\db.sqlite3" ".\db_respaldo_visual.sqlite3" -Force }
Copy-Item (Join-Path $origen "templates\*") ".\templates\" -Recurse -Force
Copy-Item (Join-Path $origen "static\*") ".\static\" -Recurse -Force
Write-Host "Interfaz actualizada. Los datos y usuarios se conservaron." -ForegroundColor Green
.\venv\Scripts\python.exe manage.py check
