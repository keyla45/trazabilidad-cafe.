$ErrorActionPreference = 'Stop'
# Ejecutar desde el directorio raíz de CaféTrace: donde existe manage.py.
if (!(Test-Path '.\manage.py')) { throw 'Abre primero la carpeta CafeTrace: no se encuentra manage.py.' }
$src = Join-Path $PSScriptRoot 'CafeTrace'
if (!(Test-Path (Join-Path $src 'cadena\empresa_views.py'))) { $src=$PSScriptRoot }
if (!(Test-Path (Join-Path $src 'cadena\empresa_views.py'))) { throw 'No se encuentran los archivos de actualización.' }
$backup = Join-Path (Get-Location) ('respaldo_empresa_demo_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
if (Test-Path '.\db.sqlite3') { Copy-Item '.\db.sqlite3' "$backup\db.sqlite3" }
$files = @(
  'cadena\urls.py','cadena\empresa_views.py','cadena\tests.py',
  'cadena\management\commands\cargar_empresa_demo.py',
  'trazabilidad\management\commands\cargar_demo_especial.py',
  'trazabilidad\views.py','cafe_trace\settings.py',
  'templates\base.html','templates\cadena\inicio.html',
  'templates\cadena\empresa_demo.html','templates\trazabilidad\publica.html',
  'static\css\empresa-demo.css','EMPRESA_SIMULADA_INSTALACION.md'
)
foreach ($f in $files) {
  $dst = Join-Path (Get-Location) $f
  $origin = Join-Path $src $f
  if (Test-Path $dst) {
    $respaldo = Join-Path $backup $f
    New-Item -ItemType Directory -Path (Split-Path $respaldo) -Force | Out-Null
    Copy-Item $dst $respaldo -Force
  }
  New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
  Copy-Item $origin $dst -Force
}
Write-Host 'Empresa DEMO instalada. Se conservaron los usuarios, la base de datos y las migraciones.' -ForegroundColor Green
Write-Host 'Ejecuta: .\venv\Scripts\python.exe manage.py check' -ForegroundColor Cyan
Write-Host 'Ejecuta: .\venv\Scripts\python.exe manage.py cargar_empresa_demo' -ForegroundColor Cyan
