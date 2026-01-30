# 📢 Sistema de Mensajería en Red Local

Sistema distribuido de mensajería corporativa para enviar notificaciones a múltiples máquinas Windows en una red local. Implementa una arquitectura maestro-esclavo.

## 🏗️ Estructura del Proyecto

```
MENSAJE/
├── backend/                    # Servidor maestro
│   └── maestro_web.py         # Servidor Flask + escaneo de red
│
├── esclavo/                    # Cliente distribuible
│   ├── esclavo.py             # Servicio que recibe mensajes
│   └── INSTRUCCIONES_Esclavo.md
│
├── frontend/                   # Interfaz web
│   ├── templates/
│   │   └── index.html         # Panel de control
│   └── static/
│       ├── script.js          # Lógica frontend
│       └── style.css          # Estilos
│
├── data/                       # Persistencia
│   └── historial_ips.json     # Base de datos de IPs
│
└── docs/                       # Documentación
    ├── README_Maestro.md      # Guía del servidor
    └── INSTRUCCIONES_Esclavo.md  # Guía del cliente
```

## 🚀 Inicio Rápido

### Configuración Inicial

```bash
# 1. Clonar o descargar el repositorio
cd MENSAJE

# 2. Crear entorno virtual (recomendado)
python -m venv .venv

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar el Servidor Maestro

```bash
# Desde la carpeta raíz del proyecto
python backend/maestro_web.py

# Abrir navegador en:
# http://localhost:8080
```

### Generar Ejecutable del Cliente Esclavo

```bash
# Activar entorno virtual primero (si no está activo)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Generar ejecutable
pyinstaller --onefile --noconsole esclavo/esclavo.py

# El ejecutable estará en: dist/esclavo.exe
# Distribuirlo a las máquinas de la red
```

## 📋 Componentes

### 🖥️ Maestro

- **Puerto Web**: 8080
- **Puerto TCP**: 5000
- **Funcionalidad**: Escanea red, envía mensajes, interfaz web

### 💻 Esclavo

- **Puerto**: 5000
- **Funcionalidad**: Escucha mensajes, muestra alertas GUI

## 📖 Documentación

- **[README_Maestro.md](docs/README_Maestro.md)**: Configuración y uso del servidor
- **[INSTRUCCIONES_Esclavo.md](docs/INSTRUCCIONES_Esclavo.md)**: Instalación del cliente

## ⚙️ Tecnologías

- **Backend**: Python, Flask, Socket, ThreadPoolExecutor
- **Frontend**: HTML5, CSS3, JavaScript ES6, EventSource
- **Cliente**: Python, Tkinter, Socket

## 🔒 Seguridad

- Solo accesible en red local
- Límite de mensaje: 2048 bytes
- Timeout de conexión: 0.3s
- Validación de entrada

## 📝 Licencia

Proyecto interno corporativo.
