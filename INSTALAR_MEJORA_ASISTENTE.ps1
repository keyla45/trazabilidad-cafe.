# Se ejecuta desde la carpeta original CafeTrace; nunca borra db.sqlite3 ni migraciones.
$ErrorActionPreference='Stop'
if (-not (Test-Path '.\manage.py')) { throw 'Entra a la carpeta original CafeTrace antes de instalar.' }
$origen=Join-Path $PSScriptRoot 'CafeTrace'
if (-not (Test-Path $origen)) { $origen=$PSScriptRoot }
$archivos=@('cadena\innovacion.py','cadena\tests_asistente_mejorado.py','templates\cadena\innovacion.html','static\css\innovacion.css','static\js\innovacion.js','GUIA_ASISTENTE_INTERACTIVO.md')
$respaldo=Join-Path (Get-Location) ('respaldo_asistente_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $respaldo -Force | Out-Null
foreach($rel in $archivos){
 $fuente=Join-Path $origen $rel
 if (-not (Test-Path $fuente)) { throw "Falta archivo del paquete: $rel" }
 $dest=Join-Path (Get-Location) $rel
 if (Test-Path $dest) {
   $anterior=Join-Path $respaldo $rel
   New-Item -ItemType Directory -Path (Split-Path $anterior) -Force | Out-Null
   Copy-Item $dest $anterior -Force
 }
 New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
 Copy-Item $fuente $dest -Force
}
Write-Host "ASISTENTE ACTUALIZADO. Respaldo: $respaldo" -ForegroundColor Green
Write-Host 'Ahora ejecuta las pruebas Django indicadas en GUIA_ASISTENTE_INTERACTIVO.md'
