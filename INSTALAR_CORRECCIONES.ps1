# Ejecutar desde C:\Users\PC_1\Desktop\CafeTrace en PowerShell
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$proyecto = (Get-Location).Path
if (-not (Test-Path (Join-Path $proyecto 'manage.py'))) { throw 'Abra PowerShell en la carpeta CafeTrace, junto a manage.py.' }
$carpeta = Join-Path $proyecto ('respaldo_parche_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $carpeta | Out-Null
$archivos = @('cadena/innovacion.py','cadena/views.py','cadena/tests.py','trazabilidad/permissions.py','trazabilidad/views.py','trazabilidad/especial_views.py','trazabilidad/integracion_views.py','cafe_trace/settings.py')
foreach($f in $archivos){
  $rel = $f.Replace('/', [IO.Path]::DirectorySeparatorChar)
  $destino = Join-Path $proyecto $rel
  $fuente = Join-Path $raiz $rel
  if(-not (Test-Path $destino)){ throw "No se encontró el archivo actual: $f" }
  $respaldo = Join-Path $carpeta $rel
  New-Item -ItemType Directory -Path (Split-Path -Parent $respaldo) -Force | Out-Null
  Copy-Item $destino $respaldo -Force
  Copy-Item $fuente $destino -Force
}
Write-Host 'Parche instalado. Copia de seguridad en:' $carpeta -ForegroundColor Green
Write-Host 'Ahora ejecute .\venv\Scripts\python.exe manage.py check y manage.py test cadena'
