import subprocess
import socket
import json
import os
import platform
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configuración
RED = os.environ.get("NETWORK_PREFIX", "10.6")
PATRON = os.environ.get("HOSTNAME_PATTERN", "TESO-")
WORKERS = int(os.environ.get("SCAN_WORKERS", "100"))
INTERVALO = int(os.environ.get("SCAN_INTERVAL", "300"))  # 5 minutos
ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "machines.json"
)

# Detectar sistema operativo para comando ping
IS_WINDOWS = platform.system().lower() == "windows"
PING_COUNT_FLAG = "-n" if IS_WINDOWS else "-c"
PING_TIMEOUT_FLAG = "-w" if IS_WINDOWS else "-W"
PING_TIMEOUT_VALUE = "150" if IS_WINDOWS else "1"


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def ping_y_resolver(ip):
    """Hace ping a una IP y si responde, busca su hostname"""
    try:
        result = subprocess.run(
            ["ping", PING_COUNT_FLAG, "1", PING_TIMEOUT_FLAG, PING_TIMEOUT_VALUE, ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        if result.returncode == 0:
            hostname = socket.gethostbyaddr(ip)[0].upper()
            if hostname.startswith(PATRON):
                return (hostname, ip)
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return None


def guardar_maquina(hostname, ip):
    """Guarda una máquina encontrada inmediatamente en el JSON"""
    try:
        # Leer archivo actual
        data = {}
        if os.path.exists(ARCHIVO):
            with open(ARCHIVO, "r") as f:
                data = json.load(f)

        # Agregar/actualizar máquina
        data[hostname] = {
            "ip": ip,
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Guardar
        os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
        with open(ARCHIVO, "w") as f:
            json.dump(data, f, indent=2)

        log(f"[OK] {hostname} -> {ip}")
    except Exception as e:
        log(f"[ERROR] Guardando: {e}")


def escanear():
    """Escanea toda la red configurada"""
    log(f"Iniciando escaneo {RED}.x.x buscando {PATRON}*")

    for octeto in range(256):
        log(f"Segmento {RED}.{octeto}.x")
        ips = [f"{RED}.{octeto}.{host}" for host in range(1, 255)]

        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for resultado in executor.map(ping_y_resolver, ips):
                if resultado:
                    guardar_maquina(*resultado)

    log("Escaneo completado")


if __name__ == "__main__":
    log(f"Discovery Service - Red {RED}.x.x | Patron {PATRON}*")
    log(f"Sistema: {platform.system()} | Workers: {WORKERS} | Intervalo: {INTERVALO}s")

    while True:
        escanear()
        log(f"Proximo escaneo en {INTERVALO}s")
        try:
            import time

            time.sleep(INTERVALO)
        except KeyboardInterrupt:
            log("Detenido por usuario")
            break
