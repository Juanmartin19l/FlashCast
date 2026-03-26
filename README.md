# ⚡ FlashCast

Sistema de mensajería distribuida para enviar notificaciones instantáneas a múltiples equipos en una red local. Perfecto para entornos corporativos y departamentos de TI.

## ✨ Features

- 🚀 Transmisión masiva (500+ equipos simultáneamente)
- 🌐 Interfaz web moderna
- 📡 Monitoreo en tiempo real
- 🗂️ Gestión de dispositivos en NocoDB
- 🛑 Control de cancelación de envíos

## 🏗️ Project Structure

```tree
FlashCast/
├── servidor/                   # Broadcast server
│   ├── backend/
│   │   ├── servidor.py        # Flask server + message sender
│   ├── frontend/              # Web interface
│   │   ├── templates/
│   │   │   └── index.html     # Control panel
│   │   └── static/
│   │       ├── script.js      # Frontend logic
│   │       └── style.css      # Styles
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

### 2. Ejecutar Servidor Web (en Docker)

```bash
cd servidor/
docker compose up --build
```

Acceder a: **<http://localhost:8080>**

### 3. Configurar NocoDB

Configura `servidor/.env` con tu URL y token de NocoDB:

- `NOCODB_BASE_URL`
- `NOCODB_API_TOKEN`
- `NOCODB_ORG`
- `NOCODB_PROJECT`
- `NOCODB_TABLE=dispositivos`

### 4. Generar Cliente (.exe)

```bash
pyinstaller --onefile --noconsole --icon=cliente/flashcast.ico cliente/cliente.py
```

El ejecutable estará en `dist/cliente.exe` - distribuir a los equipos de la red.

## Stack Tecnológico

**Servidor:** Python, Flask, Socket, ThreadPoolExecutor  
**Frontend:** HTML5, CSS3, JavaScript ES6  
**Cliente:** Python, Tkinter, PyInstaller
