$ErrorActionPreference = 'Stop'
$proyecto = (Get-Location).Path
if (-not (Test-Path (Join-Path $proyecto 'manage.py'))) { throw 'Ejecuta este instalador desde la carpeta CafeTrace que tiene manage.py' }
$fuente = Join-Path $PSScriptRoot 'cadena\innovacion.py'
$destino = Join-Path $proyecto 'cadena\innovacion.py'
if (-not (Test-Path $destino)) { throw 'No se encontró cadena\innovacion.py. Actualiza primero el proyecto de 1 diciembre.' }
$backup = Join-Path $proyecto ('innovacion_respaldo_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.py')
Copy-Item $destino $backup
Copy-Item $fuente $destino -Force
Write-Host 'Parche instalado y respaldo guardado.' -ForegroundColor Green
& '.\venv\Scripts\python.exe' manage.py test cadena
