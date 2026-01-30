# ⚡ FlashCast

Sistema de mensajería distribuida para enviar notificaciones instantáneas a múltiples equipos en una red local. Perfecto para entornos corporativos y departamentos de TI.

## ✨ Features

- 🚀 Transmisión masiva (500+ equipos simultáneamente)
- 🌐 Interfaz web moderna
- 📡 Monitoreo en tiempo real
- 🔍 Descubrimiento automático de red (hostname pattern TESO-\*)
- 💾 Persistencia de máquinas en machines.json
- 🛑 Control de cancelación de envíos
- 🔄 Escaneo periódico en background (discovery service)

## 🏗️ Project Structure

```tree
FlashCast/
├── servidor/                   # Broadcast server
│   ├── backend/
│   │   ├── servidor.py        # Flask server + message sender
│   │   └── discovery_service.py  # Network discovery service (runs separately)
│   ├── frontend/              # Web interface
│   │   ├── templates/
│   │   │   └── index.html     # Control panel
│   │   └── static/
│   │       ├── script.js      # Frontend logic
│   │       └── style.css      # Styles
│   └── data/                  # Persistence
│       └── machines.json      # Hostname -> IP mapping
│
├── cliente/                    # Client agent
│   ├── cliente.py             # Message receiver service
│   ├── flashcast.ico          # Icon for executable
│   └── INSTRUCCIONES_Cliente.md
│
└── docs/                       # Documentation
    ├── INSTRUCCIONES_Servidor.md     # Server guide
    └── INSTRUCCIONES_Cliente.md      # Client guide
```

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar repositorio
cd FlashCast

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar Discovery Service (en background)

**Importante:** Este servicio debe ejecutarse continuamente para mantener actualizada la lista de máquinas.

```bash
# Opción 1: Ejecución en terminal (mantener abierto)
python servidor/backend/discovery_service.py

# Opción 2: Ejecución como servicio de Windows (recomendado)
# Usar Task Scheduler o nssm para ejecutar al inicio
```

El servicio escanea la red cada 5 minutos buscando máquinas con patrón **TESO-\***.

### 3. Ejecutar Servidor Web

```bash
python servidor/backend/servidor.py
```

Acceder a: **<http://localhost:8080>**

### 4. Generar Cliente (.exe)

```bash
pyinstaller --onefile --noconsole --icon=cliente/flashcast.ico cliente/cliente.py
```

El ejecutable estará en `dist/cliente.exe` - distribuir a los equipos de la red.

## Stack Tecnológico

**Servidor:** Python, Flask, Socket, ThreadPoolExecutor  
**Frontend:** HTML5, CSS3, JavaScript ES6, SSE  
**Cliente:** Python, Tkinter, PyInstaller
