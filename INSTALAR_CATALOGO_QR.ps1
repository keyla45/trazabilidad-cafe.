$ErrorActionPreference = 'Stop'
if (!(Test-Path '.\manage.py')) { throw 'Primero ubícate en la carpeta CafeTrace (donde está manage.py).' }
$source = $PSScriptRoot
if (!(Test-Path (Join-Path $source 'cadena\publico_views.py'))) { $source = Join-Path $PSScriptRoot 'CafeTrace' }
if (!(Test-Path (Join-Path $source 'cadena\publico_views.py'))) { throw 'No encuentro el código del catálogo en el ZIP.' }
$backup = Join-Path (Get-Location) ('respaldo_publico_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$files = @('cafe_trace\urls.py','cadena\publico_views.py','cadena\tests.py','trazabilidad\views.py','templates\registration\login.html','templates\base.html','templates\publico\catalogo.html','templates\publico\cafe.html','static\css\publico-cafe.css','INICIAR_CAFETRACE_RED.ps1')
foreach ($f in $files) {
   $src = Join-Path $source $f
   $dst = Join-Path (Get-Location) $f
   if (Test-Path $dst) {
      $previo = Join-Path $backup $f
      New-Item -ItemType Directory -Path (Split-Path $previo) -Force | Out-Null
      Copy-Item -LiteralPath $dst -Destination $previo -Force
   }
   New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
   Copy-Item -LiteralPath $src -Destination $dst -Force
}
Write-Host 'CATÁLOGO Y QR INSTALADOS. Base de datos y usuarios conservados.' -ForegroundColor Green
Write-Host 'Para probar: .\venv\Scripts\python.exe manage.py test cadena' -ForegroundColor Cyan
Write-Host 'Para celulares: .\INICIAR_CAFETRACE_RED.ps1' -ForegroundColor Cyan
