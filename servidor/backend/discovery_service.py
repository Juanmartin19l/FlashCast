import subprocess
import socket
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configuración
RED = "10.6"
PATRON = "TESO-"
WORKERS = 100
INTERVALO = 300  # 5 minutos
ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "machines.json"
)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def ping_y_resolver(ip):
    """Hace ping a una IP y si responde, busca su hostname"""
    try:
        if (
            subprocess.run(
                ["ping", "-n", "1", "-w", "150", ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).returncode
            == 0
        ):
            hostname = socket.gethostbyaddr(ip)[0].upper()
            if hostname.startswith(PATRON):
                return (hostname, ip)
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

        log(f"✅ {hostname} -> {ip}")
    except Exception as e:
        log(f"❌ Error guardando: {e}")


def escanear():
    """Escanea toda la red 10.6.x.x"""
    log(f"🚀 Escaneando {RED}.x.x buscando {PATRON}*")

    for octeto in range(256):
        log(f"🔍 Segmento {RED}.{octeto}.x")
        ips = [f"{RED}.{octeto}.{host}" for host in range(1, 255)]

        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for resultado in executor.map(ping_y_resolver, ips):
                if resultado:
                    guardar_maquina(*resultado)

    log("✅ Escaneo completado")


if __name__ == "__main__":
    log(f"🎯 Discovery Service - Red {RED}.x.x | Patrón {PATRON}*")

    while True:
        escanear()
        log(f"⏱️  Próximo escaneo en {INTERVALO}s")
        try:
            import time

            time.sleep(INTERVALO)
        except KeyboardInterrupt:
            log("👋 Detenido")
            break
