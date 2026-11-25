# Ejecutar desde la carpeta original de CafeTrace, con servidor detenido.
$ErrorActionPreference='Stop'
if (-not (Test-Path '.\manage.py')) { throw 'Abre la terminal dentro de C:\Users\PC_1\Desktop\CafeTrace antes de continuar.' }
$origen=Join-Path $PSScriptRoot 'CafeTrace'
if (-not (Test-Path $origen)) { $origen=$PSScriptRoot }
$archivos=@(
'cadena\urls.py',
'cadena\publico_views.py',
'cadena\chatbot_publico.py',
'cadena\estadisticas.py',
'cadena\tests_estadisticas_chat.py',
'templates\base.html',
'templates\cadena\estadisticas.html',
'templates\cadena\innovacion.html',
'templates\publico\catalogo.html',
'templates\publico\producto.html',
'templates\publico\cafe.html',
'static\css\chat-publico.css',
'static\css\estadisticas-cafe.css',
'static\css\innovacion.css',
'static\js\chat-publico.js',
'static\js\estadisticas-cafe.js',
'LEEME_CHAT_CATALOGO_ESTADISTICAS.md'
)
# Comprobar todo antes de tocar los archivos actuales.
foreach($rel in $archivos) { if(-not (Test-Path (Join-Path $origen $rel))) {throw "Paquete incompleto: $rel"} }
$respaldo=Join-Path (Get-Location) ('respaldo_catalogo_estadisticas_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $respaldo -Force | Out-Null
foreach($rel in $archivos) {
  $destino=Join-Path (Get-Location) $rel
  $fuente=Join-Path $origen $rel
  if (Test-Path $destino) {
    $destino_backup=Join-Path $respaldo $rel
    New-Item -ItemType Directory -Path (Split-Path $destino_backup) -Force | Out-Null
    Copy-Item $destino $destino_backup -Force
  }
  New-Item -ItemType Directory -Path (Split-Path $destino) -Force | Out-Null
  Copy-Item $fuente $destino -Force
}
Write-Host "ACTUALIZACION INSTALADA. Respaldo: $respaldo" -ForegroundColor Green
Write-Host 'Sin cambios en modelos ni base de datos. Ejecuta los comandos de prueba de la guía.'
