# ⚡ FlashCast Server - Broadcast Control Panel

## Overview

The **FlashCast Server** is a Flask web server that enables mass messaging to all machines on the local network that have the **FlashCast Client** installed and running.

## Características

- 🌐 **Interfaz Web Moderna**: Panel de control accesible desde el navegador
- 🔍 **Descubrimiento de Máquinas**: Detecta dispositivos en la red local (ejecutado localmente)
- 📨 **Envío Masivo Concurrente**: Utiliza 500 hilos para envío rápido
- 💾 **Persistencia de Máquinas**: Guarda máquinas en machines.json
- 📡 **Actualizaciones en Tiempo Real**: Server-Sent Events (SSE) para logs dinámicos
- 🛑 **Cancelación de Envíos**: Posibilidad de detener un envío en progreso
- 🐳 **Containerizado**: Ejecuta en Docker para fácil despliegue

## Requisitos

- Python 3.12+
- Docker y Docker Compose (para el servidor)
- Flask (para discovery_service local)
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

### 3. Ejecutar Discovery Service (Local)

**En otra terminal**, ejecuta:

```bash
python servidor/backend/discovery_service.py
```

Este servicio escanea la red cada 5 minutos buscando máquinas con patrón **TESO-\*** y actualiza `machines.json`.

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

### Discovery Service

Las variables de entorno pueden configurarse en el terminal:

```bash
# Red a escanear (por defecto: 10.6)
set NETWORK_PREFIX=10.6  # Windows
export NETWORK_PREFIX=10.6  # Linux/Mac

# Patrón de hostname (por defecto: TESO-)
set HOSTNAME_PATTERN=TESO-  # Windows
export HOSTNAME_PATTERN=TESO-  # Linux/Mac

# Intervalo de escaneo en segundos (por defecto: 300 = 5 minutos)
set SCAN_INTERVAL=300  # Windows
export SCAN_INTERVAL=300  # Linux/Mac

# Número de workers para el escaneo (por defecto: 100)
set SCAN_WORKERS=100  # Windows
export SCAN_WORKERS=100  # Linux/Mac
```

## Estructura de Archivos

```
backend/
  └── maestro_web.py       # Servidor principal

frontend/
  ├── templates/
  │   └── index.html       # Interfaz web
  └── static/
      ├── script.js        # Lógica del frontend
      └── style.css        # Estilos

data/
  └── historial_ips.json   # Base de datos de IPs contactadas
```

## Funcionalidad Técnica

### Flujo de Envío

1. Usuario escribe mensaje y presiona "Enviar"
2. Maestro valida el mensaje (max 2048 bytes UTF-8)
3. **Primera fase**: Envía a IPs del historial (conocidas)
4. **Segunda fase**: Escanea toda la red local (rango /16)
5. Cada IP que responde se guarda en `historial_ips.json`
6. Los logs se transmiten en tiempo real vía SSE

### API Endpoints

- `GET /` - Interfaz web principal
- `POST /api/enviar` - Iniciar envío de mensaje
- `POST /api/cancelar` - Cancelar envío en progreso
- `GET /api/stream` - Stream SSE de logs
- `GET /api/estadisticas` - Obtener estadísticas actuales

### Tipos de Logs

- 🟢 **Nueva**: IP contactada por primera vez (verde)
- 🔵 **Repetida**: IP ya existente en historial (azul)
- ℹ️ **Info**: Mensajes informativos (gris)
- ✅ **Success**: Operación exitosa (verde)
- ❌ **Error**: Errores durante el envío (rojo)

## Seguridad y Notas

- El servidor solo es accesible desde la red local
- Los mensajes están limitados a 2048 bytes
- El timeout de 0.3s evita bloqueos en IPs inactivas
- El historial persiste entre reinicios del servidor

## Solución de Problemas

### El servidor Docker no inicia

- Verifica que el puerto 8080 no esté en uso: `netstat -ano | findstr :8080`
- Verifica que Docker esté corriendo
- Revisa los logs: `docker compose logs`

### Discovery Service no encuentra máquinas

- Verifica que estés ejecutándolo en tu máquina local (NO en Docker)
- Verifica el patrón de hostname: `ipconfig /all` (Windows) o `ifconfig` (Linux/Mac)
- Ajusta `NETWORK_PREFIX` si tu red no es `10.6.x.x`
- Verifica el firewall local permite ping

### Los mensajes no llegan a los clientes

- Verifica que el firewall permita conexiones TCP al puerto 5000
- Confirma que los clientes estén ejecutándose
- Revisa los logs en tiempo real en la interfaz web
- Verifica que las máquinas están en `machines.json`

### El escaneo es muy lento

- Aumenta `SCAN_WORKERS` (ej: 200)
- Reduce `PING_TIMEOUT_VALUE` en discovery_service.py
- Considera reducir el rango de IPs a escanear en `NETWORK_PREFIX`

## Mantenimiento

### Limpiar Historial

Para reiniciar el historial de IPs, simplemente elimina o vacía el archivo:

```bash
rm servidor/data/historial_ips.json
```

El archivo se recreará automáticamente en el próximo envío.

### Ver Logs del Servidor

Los logs del servidor aparecen en la consola donde ejecutaste `maestro_web.py`.

## Integración con Esclavo

Ver [INSTRUCCIONES_Esclavo.md](INSTRUCCIONES_Esclavo.md) para configurar los clientes.
