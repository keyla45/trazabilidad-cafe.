# CaféTrace: chatbot público y analítica temporal

## Novedades
- Catálogo sin inicio de sesión con chatbot flotante en las mismas páginas. Consulta marcas, variedades, fincas, procesos registrados, precios publicados, gramajes y QR.
- El chatbot público **no** consulta saldos internos, pedidos, clientes privados o MRP. Utiliza reglas y registros publicados; no es una IA generativa ni responde fuera del alcance documentado.
- Estadísticas internas: `/estadisticas/` y API privada `/api/estadisticas/`; evolución de seis meses en ventas, ingresos registrados, pedidos, lotes, entradas y salidas de inventario. Comparación mes actual parcial versus mes anterior completo.
- Los datos DEMO son ficticios. Los precios y ventas simuladas no son resultados científicos.
- El catálogo abre fichas en la misma pestaña; el chatbot conserva enlaces dentro del sitio.

## Instalación
1. Respalda `db.sqlite3`, `venv`, las migraciones y el proyecto.
2. Detén `runserver` con Ctrl+C.
3. Desde la carpeta `CafeTrace`, instala con el script `INSTALAR_MEJORAS_CHAT_ESTADISTICAS.ps1` del ZIP.
4. Ejecuta los comandos **uno por uno**:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test cadena.tests_estadisticas_chat
.\venv\Scripts\python.exe manage.py runserver
```

5. Visita `http://127.0.0.1:8000/explorar/` y abre el chatbot. Para administración, inicia sesión y visita `/estadisticas/`.

## Datos y seguridad
La actualización no cambia los modelos: no necesita migraciones. El chatbot público cuenta con límite básico por sesión, no debe recibir datos personales, y la analítica del negocio exige login y permisos. Para producción, añade protección de infraestructura y despliega con HTTPS.
