# CaféTrace UPEC — Entrega del 1 de diciembre de 2026

## Qué incluye
- Proyecto Django de cinco áreas y trazabilidad de lotes por QR, aprovechando el código anterior.
- Centro `/herramientas/`: indicadores, gráfico por método, consultas de inventario, chatbot basado en reglas, asistente guiado y dictado por voz cuando el navegador lo soporte.
- API JSON de solo lectura: `/api/resumen/` y `/api/lote/CODIGO/` (ambas requieren sesión y permisos).
- Comando `configurar_usuarios_demo`, que asigna nombres y grupos a usuarios de prueba existentes; no cambia contraseñas.
- `ENTREGA_01_DICIEMBRE/`: protocolo presencial, hojas de registro, borrador de informe de resultados y guion de exposición.
- Pruebas automáticas Django añadidas en `cadena/tests.py`.

## Importante
La herramienta de consulta **no es un LLM**; responde por reglas y datos del aplicativo. El dictado se apoya en reconocimiento de voz del navegador y puede no estar disponible. El MRP representa una parte del funcionamiento ERP, pero no equivale a Odoo ni está conectado a Odoo. No existe un enlace público ni una validación presencial ejecutada por el asistente. No se fabricaron fotografías, resultados ni videos de pruebas.

## Instalación segura de actualización
1. Descargar `CafeTrace_UPEC_Entrega_01_Diciembre_2026.zip` sin cambiar su nombre.
2. En VS Code abrir la carpeta antigua de CaféTrace, detener el servidor con `Ctrl+C`.
3. Copiar el archivo `INSTALAR_ACTUALIZACION_2026.ps1` del ZIP a la carpeta antigua o ejecutar el bloque de instalación proporcionado en la conversación.
4. Ejecutar en PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`; después `.\INSTALAR_ACTUALIZACION_2026.ps1`.
5. Ejecutar **por separado**:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py crear_roles
.\venv\Scripts\python.exe manage.py configurar_usuarios_demo
.\venv\Scripts\python.exe manage.py test cadena
.\venv\Scripts\python.exe manage.py runserver
```

Visitar http://127.0.0.1:8000/herramientas/ con usuario administrador.

## Para despliegue real
No publicar el servidor de desarrollo con `DEBUG=1`. Configurar SECRET_KEY de producción, `ALLOWED_HOSTS`, HTTPS, archivos estáticos, copias de seguridad y base de datos de despliegue. La URL pública se entrega solo cuando se comprueba desde otro dispositivo y su persistencia está garantizada.
