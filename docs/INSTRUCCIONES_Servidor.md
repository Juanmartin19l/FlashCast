# ⚡ FlashCast Server - Broadcast Control Panel

## Overview

The **FlashCast Server** is a Flask web server that enables mass messaging to all machines on the local network that have the **FlashCast Client** installed and running.

## Características

- 🌐 **Interfaz Web Moderna**: Panel de control accesible desde el navegador
- 🔍 **Escaneo Automático de Red**: Detecta automáticamente dispositivos en la red local
- 📨 **Envío Masivo Concurrente**: Utiliza 500 hilos para envío rápido
- 💾 **Historial Inteligente**: Guarda IPs contactadas para priorizar en próximos envíos
- 📡 **Actualizaciones en Tiempo Real**: Server-Sent Events (SSE) para logs dinámicos
- 🛑 **Cancelación de Envíos**: Posibilidad de detener un envío en progreso

## Requisitos

- Python 3.x
- Flask (`pip install flask`)
- Acceso a la red local

## Instalación y Uso

### 1. Configurar el Entorno

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

### 2. Run the Server

```bash
# From the project root
python servidor/servidor.py
```

The server will start on:

- **Web Interface**: http://localhost:8080
- **TCP Server**: Port 5000 (client communication)

### 3. Acceder al Panel

Abre tu navegador y ve a: **http://localhost:8080**

### 4. Enviar Mensajes

1. Escribe el mensaje en el área de texto
2. El mensaje soporta formato markdown simplificado:
   - `# Título` para encabezados
   - `**Texto**` para negritas
3. Haz clic en **"ENVIAR MENSAJE A TODA LA RED"**
4. Observa el log en tiempo real de las IPs contactadas
5. Puedes cancelar el envío en cualquier momento

## Configuration

Constants can be adjusted at the top of `servidor/servidor.py`:

```python
PUERTO = 5000              # TCP port for client communication
TIMEOUT = 0.3              # Connection timeout (seconds)
MAX_HILOS = 500            # Concurrent threads for sending
MAX_CARACTERES = 2048      # Message character limit
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

### El servidor no inicia

- Verifica que el puerto 8080 no esté en uso
- Verifica que el puerto 5000 esté libre
- Comprueba que Flask esté instalado

### Los mensajes no llegan a los esclavos

- Verifica que el firewall permita conexiones TCP al puerto 5000
- Confirma que los esclavos estén ejecutándose
- Revisa los logs del servidor en la consola

### El escaneo es muy lento

- Ajusta `TIMEOUT` a un valor menor (ej: 0.2)
- Aumenta `MAX_HILOS` para más concurrencia
- Considera reducir el rango de IPs a escanear

## Mantenimiento

### Limpiar Historial

Para reiniciar el historial de IPs, simplemente elimina o vacía el archivo:

```bash
rm data/historial_ips.json
```

El archivo se recreará automáticamente en el próximo envío.

### Ver Logs del Servidor

Los logs del servidor aparecen en la consola donde ejecutaste `maestro_web.py`.

## Integración con Esclavo

Ver [INSTRUCCIONES_Esclavo.md](INSTRUCCIONES_Esclavo.md) para configurar los clientes.
