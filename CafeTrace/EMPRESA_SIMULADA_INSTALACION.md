# CaféTrace — Empresa cafetera ficticia «Origen y Taza»

**Objetivo:** representar una cadena completa con finca, beneficio, producción, almacén, distribución y tienda, con datos ficticios enlazados a los mismos lotes. La simulación NO es evidencia de operación real ni de resultados de investigación.

## Instalación segura, sin perder tus registros

1. Detén Django (`Ctrl+C`). Haz copia de seguridad de la carpeta y de `db.sqlite3`.
2. Usa el instalador PowerShell incluido (`INSTALAR_EMPRESA_DEMO.ps1`) desde la carpeta de tu proyecto. NO reemplaces ni borres `db.sqlite3`, `venv` o tus migraciones.
3. En PowerShell, ejecuta por separado:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py cargar_empresa_demo
.\venv\Scripts\python.exe manage.py test cadena
.\venv\Scripts\python.exe manage.py runserver
```

4. Abre `http://127.0.0.1:8000/empresa/`. Entra como administrador o un usuario autorizado. Usa los botones de cada lote para abrir el proceso, el pasaporte o la imagen QR.

## Contenido de ejemplo

- Productor Juan Pérez (ficticio), finca «La Esperanza» (ficticia), origen de 4 lotes sintéticos.
- María Torres: acopio y beneficio; Carlos Méndez: producción; Lucía Herrera: inventario; David Rosero: entrega; Andrea Rosales: tienda.
- Procesos de beneficio lavado, natural, honey y anaeróbico (registros de ejemplo). No todas las etapas están finalizadas, deliberadamente.
- Bodega, MRP, presentaciones 250/500/1000 g, ventas y puntos de venta.
- Tienda ficticia «Origen y Taza» en Tulcán; **no se afirma que exista una tienda física en esa dirección**.

El comando es idempotente respecto a las claves de registros DEMO que crea: puedes volver a ejecutarlo sin duplicar los registros de la demostración. No establece contraseñas de usuarios ni publica información privada.

## QR desde un teléfono

La URL dentro del QR necesita ser accesible desde el dispositivo de lectura. `127.0.0.1` solo apunta al dispositivo donde se abre.

En la misma red Wi-Fi, averigua tu IPv4 con `ipconfig`. Después, desde la carpeta del aplicativo:

```powershell
$env:CAFETRACE_ALLOWED_HOSTS="127.0.0.1,localhost,192.168.1.10"
$env:CAFETRACE_PUBLIC_BASE_URL="http://192.168.1.10:8000"
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

**Sustituye `192.168.1.10` por la dirección IPv4 REAL de tu PC.** El celular debe estar en la misma red y el firewall debe permitir el acceso al puerto 8000. Vuelve a generar el QR tras configurar la URL. No expongas el servidor de desarrollo a Internet: para publicación usa despliegue seguro con HTTPS, `DEBUG=0`, `SECRET_KEY` propia y configuración de hosts.

## Comprobación de la exposición

1. Administrador visita `/empresa/` y elige un lote DEMO.
2. Consulta la finca, el proceso, la calidad, la recepción y la existencia.
3. Comprueba los pedidos y el registro de despacho.
4. Escanea el QR y presenta el pasaporte digital desde otro dispositivo.
5. Distingue claramente los registros DEMO de la validación real con usuarios, que debe ejecutarse y documentarse por separado.

Si `manage.py test cadena` falla, conserva la salida completa antes de presentar la demostración como verificada. No se han ejecutado las pruebas de Django en el entorno de construcción.
