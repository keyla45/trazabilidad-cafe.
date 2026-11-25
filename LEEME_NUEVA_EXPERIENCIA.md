# CaféTrace — Cinco áreas grandes y vistas por rol

Actualización de interfaz para el proyecto Django, basada en el documento TICS aplicativo café.docx.

- Administrador: centro de control y navegación lateral con las cinco áreas.
- Usuario operativo: sin barra lateral administrativa; menú superior compacto y redirección a su área.
- Cinco tarjetas con fotografía, título y descripción ampliados.
- Paneles internos con fotografía, herramientas, información y accesos funcionales existentes.
- Datos DEMO separados de mediciones reales. No se inventan valores para los KPI.

## Instalar desde PowerShell

1. Descarga el ZIP con su nombre original.
2. Abre VS Code en la carpeta que contiene `manage.py` y detén `runserver` con Ctrl+C.
3. En PowerShell ejecuta:

```powershell
$zip = Get-ChildItem $env:USERPROFILE -Recurse -File -Filter 'CafeTrace_UPEC_5_Areas_Experiencia_2026.zip' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $zip) { throw 'Descarga primero el archivo ZIP.' }
$temporal = Join-Path $env:TEMP 'cafetrace_entrega_5_areas'
Expand-Archive -LiteralPath $zip.FullName -DestinationPath $temporal -Force
& (Join-Path $temporal 'CafeTrace\INSTALAR_NUEVA_EXPERIENCIA.ps1')
```

Si PowerShell bloquea scripts, **alternativa sin ejecutar un archivo ps1** (realiza primero copia de seguridad de templates y static):

```powershell
Copy-Item "$temporal\CafeTrace\templates\*" ".\templates\" -Recurse -Force
Copy-Item "$temporal\CafeTrace\static\*" ".\static\" -Recurse -Force
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py runserver
```

**Importante:** esta entrega es principalmente de interfaz y navegación. Se preservan los módulos y operaciones del último ZIP Cinco Paneles Admin; no crea sensores ni funciones contables nuevas. No se necesita `makemigrations` al instalar solo la interfaz.
