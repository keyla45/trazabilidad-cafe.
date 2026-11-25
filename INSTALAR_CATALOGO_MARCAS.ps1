$ErrorActionPreference = 'Stop'
if (!(Test-Path '.\manage.py')) { throw 'Abre la terminal en la carpeta CafeTrace donde se encuentra manage.py.' }
$origen=$PSScriptRoot
if (!(Test-Path (Join-Path $origen 'cadena\publico_views.py'))) { $origen=Join-Path $PSScriptRoot 'CafeTrace' }
if (!(Test-Path (Join-Path $origen 'cadena\publico_views.py'))) { throw 'No encuentro los archivos del catálogo para instalar.' }
$archivos=@(
 'cadena\models.py', 'cadena\admin.py', 'cadena\publico_views.py', 'cadena\tests_catalogo.py',
 'cadena\management\commands\cargar_catalogo_marcas.py',
 'cafe_trace\urls.py', 'templates\publico\catalogo.html', 'templates\publico\producto.html',
 'static\css\catalogo-marcas.css'
)
$respaldo=Join-Path (Get-Location) ('respaldo_marcas_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $respaldo -Force | Out-Null
foreach($rel in $archivos) {
 $src=Join-Path $origen $rel
 if (!(Test-Path $src)) { throw "No existe el archivo $rel en el ZIP" }
 $dst=Join-Path (Get-Location) $rel
 if(Test-Path $dst){$bak=Join-Path $respaldo $rel;New-Item -ItemType Directory -Path (Split-Path $bak) -Force | Out-Null;Copy-Item $dst $bak -Force}
 New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
 Copy-Item $src $dst -Force
}
Write-Host 'CODIGO DE CATALOGO INSTALADO. Usuarios y db.sqlite3 conservados.' -ForegroundColor Green
Write-Host 'SIGUIENTE: .\venv\Scripts\python.exe manage.py makemigrations cadena' -ForegroundColor Cyan
Write-Host 'SIGUIENTE: .\venv\Scripts\python.exe manage.py migrate' -ForegroundColor Cyan
Write-Host 'SIGUIENTE: .\venv\Scripts\python.exe manage.py cargar_catalogo_marcas' -ForegroundColor Cyan
Write-Host 'SIGUIENTE: .\venv\Scripts\python.exe manage.py test cadena.tests_catalogo' -ForegroundColor Cyan
