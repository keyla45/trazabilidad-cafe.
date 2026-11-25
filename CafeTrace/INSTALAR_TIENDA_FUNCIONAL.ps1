# Ejecutar desde la carpeta CafeTrace. No elimina bases de datos ni migraciones.
$ErrorActionPreference = 'Stop'
$raiz = (Get-Location).Path
if (-not (Test-Path (Join-Path $raiz 'manage.py'))) { throw 'Abre la terminal en la carpeta CafeTrace que contiene manage.py.' }
$paquete = Get-ChildItem $env:USERPROFILE -File -Recurse -Filter 'CafeTrace_UPEC_Tienda_Funcional_Visual.zip' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $paquete) { throw 'Descarga primero CafeTrace_UPEC_Tienda_Funcional_Visual.zip.' }
$destino = Join-Path $env:TEMP 'CafeTrace_Tienda_Funcional_Visual'
Expand-Archive -LiteralPath $paquete.FullName -DestinationPath $destino -Force
$origen = Join-Path $destino 'CafeTrace'
$backup = Join-Path $raiz ('respaldo_tienda_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup | Out-Null
if (Test-Path '.\db.sqlite3') { Copy-Item '.\db.sqlite3' "$backup\db.sqlite3" }
Copy-Item '.\cadena\views.py' "$backup\views.py" -Force
Copy-Item '.\cadena\urls.py' "$backup\urls.py" -Force
Copy-Item '.\templates\cadena\area.html' "$backup\area.html" -Force
Copy-Item '.\templates\base.html' "$backup\base.html" -Force
Copy-Item "$origen\cadena\views.py" '.\cadena\views.py' -Force
Copy-Item "$origen\cadena\urls.py" '.\cadena\urls.py' -Force
Copy-Item "$origen\templates\cadena\area.html" '.\templates\cadena\area.html' -Force
Copy-Item "$origen\templates\cadena\_tienda_inicio.html" '.\templates\cadena\_tienda_inicio.html' -Force
Copy-Item "$origen\templates\cadena\tienda_puntos.html" '.\templates\cadena\tienda_puntos.html' -Force
Copy-Item "$origen\templates\cadena\tienda_productos.html" '.\templates\cadena\tienda_productos.html' -Force
Copy-Item "$origen\templates\cadena\tienda_qrs.html" '.\templates\cadena\tienda_qrs.html' -Force
Copy-Item "$origen\templates\base.html" '.\templates\base.html' -Force
Copy-Item "$origen\static\css\tienda-premium.css" '.\static\css\tienda-premium.css' -Force
Write-Host 'Interfaz y rutas de tienda actualizadas. Respaldo:' $backup -ForegroundColor Green
& '.\venv\Scripts\python.exe' 'manage.py' 'check'
if ($LASTEXITCODE -ne 0) { throw 'Django detectó un problema; revisa el mensaje anterior.' }
Write-Host 'Listo. Ejecuta .\venv\Scripts\python.exe manage.py runserver' -ForegroundColor Green
