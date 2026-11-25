# Ejecutar desde C:\Users\PC_1\Desktop\CafeTrace. Mantiene base de datos y migraciones existentes.
$ErrorActionPreference = 'Stop'
$nombre = 'CafeTrace_UPEC_Entrega_01_Diciembre_2026.zip'
$zip = Get-ChildItem -Path $env:USERPROFILE -Recurse -File -Filter $nombre -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $zip) { throw 'Descarga el ZIP y vuelve a ejecutar el instalador.' }
if (-not (Test-Path '.\manage.py')) { throw 'Abre primero la carpeta original de CafeTrace en la terminal.' }
$temporal = Join-Path $env:TEMP 'CafeTrace_Entrega2026'
Expand-Archive -LiteralPath $zip.FullName -DestinationPath $temporal -Force
$src = Join-Path $temporal 'CafeTrace'
$backup = Join-Path (Get-Location) ('respaldo_pre_entrega_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
if (Test-Path '.\db.sqlite3') { Copy-Item '.\db.sqlite3' "$backup\db.sqlite3" -Force }
foreach($ruta in @('cadena','trazabilidad','templates','static','cafe_trace')) {
 if(Test-Path $ruta){Copy-Item $ruta (Join-Path $backup $ruta) -Recurse -Force}
}
# Exclusivamente código; no sobrescribir archivos de migración del usuario.
Copy-Item "$src\cadena\innovacion.py" '.\cadena\innovacion.py' -Force
Copy-Item "$src\cadena\views.py" '.\cadena\views.py' -Force
Copy-Item "$src\cadena\urls.py" '.\cadena\urls.py' -Force
Copy-Item "$src\cadena\tests.py" '.\cadena\tests.py' -Force
Copy-Item "$src\cadena\management\commands\configurar_usuarios_demo.py" '.\cadena\management\commands\configurar_usuarios_demo.py' -Force
Copy-Item "$src\trazabilidad\permissions.py" '.\trazabilidad\permissions.py' -Force
Copy-Item "$src\templates\base.html" '.\templates\base.html' -Force
Copy-Item "$src\templates\cadena\innovacion.html" '.\templates\cadena\innovacion.html' -Force
Copy-Item "$src\static\css\innovacion.css" '.\static\css\innovacion.css' -Force
Copy-Item "$src\static\js\innovacion.js" '.\static\js\innovacion.js' -Force
Copy-Item "$src\ENTREGA_01_DICIEMBRE" '.\ENTREGA_01_DICIEMBRE' -Recurse -Force
Write-Host 'Actualización instalada. Respaldo:' $backup -ForegroundColor Green
Write-Host 'Ahora ejecuta: .\venv\Scripts\python.exe manage.py check'
