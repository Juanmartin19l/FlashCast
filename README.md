# ⚡ FlashCast

Sistema de mensajería distribuida para enviar notificaciones instantáneas a múltiples equipos en una red local. Perfecto para entornos corporativos y departamentos de TI.

## ✨ Features

- 🚀 Transmisión masiva (500+ equipos simultáneamente)
- 🌐 Interfaz web moderna
- 📡 Monitoreo en tiempo real
- 🔍 Descubrimiento automático de red
- 💾 Historial de IPs para envíos optimizados
- 🛑 Control de cancelación de envíos

## 🏗️ Project Structure

```
FlashCast/
├── servidor/                   # Broadcast server
│   ├── backend/
│   │   └── servidor.py        # Flask server + network scanner
│   ├── frontend/              # Web interface
│   │   ├── templates/
│   │   │   └── index.html     # Control panel
│   │   └── static/
│   │       ├── script.js      # Frontend logic
│   │       └── style.css      # Styles
│   └── data/                  # Persistence
│       └── historial_ips.json # IP database
│
├── cliente/                    # Client agent
│   ├── cliente.py             # Message receiver service
│   ├── flashcast.ico          # Icon for executable
│   └── INSTRUCCIONES_Cliente.md
│
└── docs/                       # Documentation
    ├── README_Servidor.md     # Server guide
    └── INSTRUCCIONES_Cliente.md  # Client guide
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

### 2. Ejecutar Servidor

```bash
python servidor/backend/servidor.py
```

Acceder a: **http://localhost:8080**

### 3. Generar Cliente (.exe)

```bash
pyinstaller --onefile --noconsole --icon=cliente/flashcast.ico cliente/cliente.py
```

El ejecutable estará en `dist/cliente.exe` - distribuir a los equipos de la red.

## � Documentation

- [Server Guide](docs/INSTRUCCIONES_Servidor.md) - Detailed server configuration
- [Client Installation](docs/INSTRUCCIONES_Cliente.md) - Client deployment guide

## 🛠️ Stack Tecnológico

**Servidor:** Python, Flask, Socket, ThreadPoolExecutor  
**Frontend:** HTML5, CSS3, JavaScript ES6, SSE  
**Cliente:** Python, Tkinter, PyInstaller
