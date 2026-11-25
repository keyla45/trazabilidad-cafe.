$ErrorActionPreference='Stop'
if (-not (Test-Path '.\manage.py')) { throw 'Primero entra en la carpeta CafeTrace (donde esta manage.py).' }
$origen=Join-Path $PSScriptRoot 'CafeTrace'
if (-not (Test-Path $origen)) { $origen=$PSScriptRoot }
$archivos=@(
 'cadena\empresa_views.py',
 'cadena\urls.py',
 'cadena\management\commands\cargar_empresa_demo.py',
 'cadena\tests_empresa_areas.py',
 'templates\cadena\empresa_demo.html',
 'templates\cadena\empresa_area.html',
 'static\css\empresa-operaciones.css'
)
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$respaldo=Join-Path (Get-Location) "respaldo_cinco_areas_$stamp"
New-Item -ItemType Directory -Path $respaldo | Out-Null
foreach ($archivo in $archivos) {
    $src=Join-Path $origen $archivo
    if (-not (Test-Path $src)) { throw "Falta archivo en ZIP: $archivo" }
    $destino=Join-Path (Get-Location) $archivo
    if (Test-Path $destino) {
        $previo=Join-Path $respaldo $archivo
        New-Item -ItemType Directory -Path (Split-Path $previo) -Force | Out-Null
        Copy-Item $destino $previo -Force
    }
    New-Item -ItemType Directory -Path (Split-Path $destino) -Force | Out-Null
    Copy-Item $src $destino -Force
}
Write-Host 'Empresa DEMO con 5 paneles actualizada. Usuarios y base de datos intactos.' -ForegroundColor Green
Write-Host "Respaldo de archivos: $respaldo"
