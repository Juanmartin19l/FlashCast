# ⚡ FlashCast Server - Broadcast Control Panel

## Overview

The **FlashCast Server** is a Flask web server that enables mass messaging to all machines on the local network that have the **FlashCast Client** installed and running.

## Características

- 🌐 **Interfaz Web Moderna**: Panel de control accesible desde el navegador
- 📨 **Envío Masivo Concurrente**: Utiliza 500 hilos para envío rápido
- 🗂️ **Persistencia en NocoDB**: Dispositivos administrados desde tabla `dispositivos`
- 🛑 **Cancelación de Envíos**: Posibilidad de detener un envío en progreso
- 🐳 **Containerizado**: Ejecuta en Docker para fácil despliegue

## Requisitos

- Python 3.12+
- Docker y Docker Compose (para el servidor)
- Acceso a la red local

## Instalación y Uso

### 1. Instalar Dependencias Locales

```bash
# Desde la carpeta raíz del proyecto

# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar el Servidor Web (Docker)

```bash
cd servidor/
docker compose up --build
```

El servidor estará disponible en:

- **Web Interface**: http://localhost:8080
- **TCP Server**: Port 5000 (comunicación con clientes)

### 3. Configurar NocoDB

En `servidor/.env` configura:

- `NOCODB_BASE_URL`
- `NOCODB_API_TOKEN`
- `NOCODB_ORG`
- `NOCODB_PROJECT`
- `NOCODB_TABLE=dispositivos`

### 4. Acceder al Panel

Abre tu navegador y ve a: **http://localhost:8080**

### 5. Enviar Mensajes

1. Escribe el mensaje en el área de texto
2. El mensaje soporta formato markdown simplificado:
   - `# Título` para encabezados
   - `**Texto**` para negritas
3. Haz clic en **"ENVIAR MENSAJE A TODA LA RED"**
4. Observa el log en tiempo real de las IPs contactadas
5. Puedes cancelar el envío en cualquier momento

## Configuración

### Servidor Web

Las constantes pueden ajustarse en `servidor/backend/servidor.py`:

```python
PUERTO = 5000              # Puerto TCP para comunicación con clientes
TIMEOUT = 0.3              # Timeout de conexión (segundos)
MAX_HILOS = 500            # Hilos concurrentes para envío
MAX_CARACTERES = 2048      # Límite de caracteres del mensaje
```

## Estructura de Archivos

```
backend/
  └── servidor.py          # Servidor principal

frontend/
  ├── templates/
  │   └── index.html       # Interfaz web
  └── static/
      ├── script.js        # Lógica del frontend
      └── style.css        # Estilos

NocoDB (tabla `dispositivos`)
  └── id, ip, nombre, departamento, fecha_registro, ultima_actualizacion
```

## Funcionalidad Técnica

### Flujo de Envío

1. Usuario escribe mensaje y presiona "Enviar"
2. Maestro valida el mensaje (max 2048 bytes UTF-8)
3. Consulta dispositivos en NocoDB
4. Envía de forma concurrente a las IPs únicas
5. Devuelve detalle de éxitos y errores

### API Endpoints

- `GET /` - Interfaz web principal
- `POST /api/enviar` - Iniciar envío de mensaje
- `POST /api/cancelar` - Cancelar envío en progreso
- `GET /api/estadisticas` - Obtener estadísticas actuales
- `GET /api/dispositivos` - Listar dispositivos
- `GET /api/dispositivos/{id}` - Obtener dispositivo
- `POST /api/dispositivos` - Crear dispositivo
- `PUT /api/dispositivos/{id}` - Actualizar dispositivo
- `DELETE /api/dispositivos/{id}` - Eliminar dispositivo

## Seguridad y Notas

- El servidor solo es accesible desde la red local
- Los mensajes están limitados a 2048 bytes
- El timeout configurable evita bloqueos en IPs inactivas

## Solución de Problemas

### El servidor Docker no inicia

- Verifica que el puerto 8080 no esté en uso: `netstat -ano | findstr :8080`
- Verifica que Docker esté corriendo
- Revisa los logs: `docker compose logs`

### NocoDB no responde

- Verifica URL y token en `servidor/.env`
- Verifica conectividad desde el contenedor al host de NocoDB
- Revisa que la tabla configurada exista y sea accesible

### Los mensajes no llegan a los clientes

- Verifica que el firewall permita conexiones TCP al puerto 5000
- Confirma que los clientes estén ejecutándose
- Revisa los logs en tiempo real en la interfaz web
- Verifica que los dispositivos existen en la tabla `dispositivos`

## Mantenimiento

### Limpiar dispositivos

Gestiona altas/bajas desde NocoDB o usando el CRUD del servidor (`/api/dispositivos`).

### Ver Logs del Servidor

Los logs del servidor aparecen en la consola donde ejecutaste `maestro_web.py`.

## Integración con Esclavo

Ver [INSTRUCCIONES_Esclavo.md](INSTRUCCIONES_Esclavo.md) para configurar los clientes.
