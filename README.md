# ⚡ FlashCast

A distributed network messaging system for broadcasting instant notifications to multiple machines on a local network. Built with a server-client architecture for corporate environments.

## 🏗️ Project Structure

```
FlashCast/
├── servidor/                   # Broadcast server
│   └── servidor.py            # Flask server + network scanner
│
├── cliente/                    # Client agent
│   ├── cliente.py             # Message receiver service
│   └── INSTRUCCIONES_Cliente.md
│
├── frontend/                   # Web interface
│   ├── templates/
│   │   └── index.html         # Control panel
│   └── static/
│       ├── script.js          # Frontend logic
│       └── style.css          # Styles
│
├── data/                       # Persistence
│   └── historial_ips.json     # IP database
│
└── docs/                       # Documentation
    ├── README_Servidor.md     # Server guide
    └── INSTRUCCIONES_Cliente.md  # Client guide
```

## 🚀 Quick Start

### Initial Setup

```bash
# 1. Clone or download the repository
cd FlashCast

# 2. Create virtual environment (recommended)
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
# From the project root
python servidor/servidor.py

# Open browser at:
# http://localhost:8080
```

### Build Client Executable

```bash
# Activate virtual environment first (if not already active)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Build executable with FlashCast icon
pyinstaller --onefile --noconsole --icon=frontend/static/flashcast.png cliente/cliente.py

# The executable will be in: dist/cliente.exe
# Distribute to network machines
```

## 📋 Components

### 🖥️ Server

- **Web Port**: 8080
- **TCP Port**: 5000
- **Features**: Network scanning, message broadcasting, web interface

### 💻 Client

- **Port**: 5000
- **Features**: Listens for messages, displays GUI alerts

## 📖 Documentation

- **[README_Servidor.md](docs/README_Servidor.md)**: Server configuration and usage
- **[INSTRUCCIONES_Cliente.md](docs/INSTRUCCIONES_Cliente.md)**: Client installation guide

## ⚙️ Technologies

- **Server**: Python, Flask, Socket, ThreadPoolExecutor
- **Frontend**: HTML5, CSS3, JavaScript ES6, EventSource
- **Client**: Python, Tkinter, Socket

## 🔒 Security

- Local network only
- Message limit: 2048 bytes
- Connection timeout: 0.3s
- Input validation

## 📝 License

Internal corporate project.
