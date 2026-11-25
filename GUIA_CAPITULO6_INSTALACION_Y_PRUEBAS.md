# CaféTrace UPEC — ampliación capítulo 6

El ZIP trae **código fuente sin base de datos ni contraseñas**. Mantiene los modelos y URLs anteriores, añade validación de sensores y transacciones de inventario y una pantalla `/laboratorio/` para medir avances. NO afirma contar con conexiones reales a Odoo, Power BI, ESP32 ni aprendizaje automático. 

## PowerShell (copiar un comando cada vez; NO copiar `(venv) PS`)

1. Respaldar el proyecto anterior y especialmente `db.sqlite3`, `venv` y `trazabilidad/migrations`.
2. Descomprimir el ZIP en otra carpeta; **fusionar** el código dentro de la carpeta del proyecto existente, sin borrar archivos que no aparecen en el ZIP.
3. Ejecutar desde la raíz del proyecto:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations trazabilidad
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py crear_roles
.\venv\Scripts\python.exe manage.py runserver
```

Abrir `http://127.0.0.1:8000/laboratorio/`, `/capitulo-6/` y `/especial/`.

Para llenar registros ficticios de café especial (solo en BD de pruebas):

```powershell
.\venv\Scripts\python.exe manage.py cargar_demo_especial
```

La pantalla E1–E3 no inventa resultados: requiere mediciones trazables.

## Ingesta de un sensor (opcional; solo ambiente de pruebas y detrás de HTTPS en producción)

Definir token temporal en PowerShell antes de iniciar el servidor:

```powershell
$env:CAFETRACE_SENSOR_TOKEN = 'CAMBIAR-POR-TOKEN-LARGO-ALEATORIO'
```

Ejemplo de petición con lote existente y sensor simulado:

```powershell
$headers = @{ 'X-CafeTrace-Token' = $env:CAFETRACE_SENSOR_TOKEN }
$body = @{ lote='CODIGO-DE-LOTE-EXISTENTE'; sensor='ESP32-demo'; variable='Humedad'; valor=11.4; unidad='%' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/iot/lectura/' -Method Post -Headers $headers -ContentType 'application/json' -Body $body
```

Este ejemplo no implica que exista un ESP32 conectado. Las lecturas son operativas, no certificadas. No expongas el servidor de desarrollo en internet.

## Límites
- Sin hardware no se valida la integración IoT.
- El modelo ML y el agente no están implementados; exigen datos suficientes, prueba y autorización.
- Odoo requiere una instancia configurada y credenciales; no existe conexión automática.
- Power BI puede consumir los CSV generados.
- E1, E2, E3 requieren datos reales separados de DEMO y evidencia experimental.
