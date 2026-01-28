import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
import threading
import queue
import time

# --- CONFIGURACIÓN ---
PUERTO = 5000
TIMEOUT = 0.3
MAX_HILOS = 500
ARCHIVO_HISTORIAL = "historial_ips.json"

app = Flask(__name__)

# Variables globales
log_queue = queue.Queue()
contador_enviados = 0
historial_ips = {}
lock = threading.Lock()
enviando = False
cancelar_envio = False


def cargar_historial():
    """Carga el historial de IPs contactadas desde el archivo"""
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error cargando historial: {e}")
            return {}
    return {}


def guardar_historial():
    """Guarda el historial de IPs contactadas en el archivo"""
    try:
        with open(ARCHIVO_HISTORIAL, "w") as f:
            json.dump(historial_ips, f, indent=2)
    except (IOError, OSError) as e:
        print(f"Error guardando historial: {e}")


def agregar_log(texto, tipo="info"):
    """Agrega una línea al log"""
    log_queue.put({"texto": texto, "tipo": tipo, "timestamp": time.time()})


def enviar_a_ip(ip, mensaje):
    global contador_enviados, cancelar_envio

    # Verificar si se canceló el envío
    if cancelar_envio:
        return False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((str(ip), PUERTO))
            s.sendall(mensaje.encode("utf-8"))

            # Registrar envío exitoso
            ip_str = str(ip)
            es_repetida = ip_str in historial_ips

            with lock:
                contador_enviados += 1
                historial_ips[ip_str] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if es_repetida:
                    agregar_log(f"🔄 {ip_str} (ya contactada antes)", "repetida")
                else:
                    agregar_log(f"✅ {ip_str} (nueva)", "nueva")

            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass
    except Exception as e:
        print(f"Error inesperado enviando a {ip}: {e}")
    return False


def obtener_mi_red():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        mi_ip = s.getsockname()[0]
        red_obj = ipaddress.ip_network(f"{mi_ip}/16", strict=False)
        return red_obj.hosts()
    finally:
        s.close()


def iniciar_bombardeo(mensaje):
    global contador_enviados, enviando, cancelar_envio

    enviando = True
    cancelar_envio = False

    with lock:
        contador_enviados = 0

    agregar_log("🚀 Iniciando envío masivo...", "info")
    agregar_log("-" * 50, "separator")

    # Primero enviar a IPs conocidas
    ips_conocidas = []
    for ip_str in historial_ips.keys():
        try:
            ips_conocidas.append(ipaddress.ip_address(ip_str))
        except ValueError:
            print(f"IP inválida en historial: {ip_str}")

    if ips_conocidas and not cancelar_envio:
        agregar_log(
            f"⚡ Enviando primero a {len(ips_conocidas)} IPs conocidas...", "info"
        )
        with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
            executor.map(lambda ip: enviar_a_ip(ip, mensaje), ips_conocidas)

        if cancelar_envio:
            agregar_log("🛑 Envío cancelado por el usuario", "error")
            enviando = False
            return

        agregar_log("✅ IPs conocidas procesadas", "success")
        agregar_log("-" * 50, "separator")

    # Luego escanear toda la red
    if not cancelar_envio:
        agregar_log("🔍 Escaneando resto de la red...", "info")
        hosts = obtener_mi_red()

        ips_conocidas_str = set(historial_ips.keys())
        hosts_nuevos = [h for h in hosts if str(h) not in ips_conocidas_str]

        with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
            executor.map(lambda ip: enviar_a_ip(ip, mensaje), hosts_nuevos)

    if cancelar_envio:
        agregar_log("🛑 Envío cancelado por el usuario", "error")
        enviando = False
        return

    guardar_historial()

    agregar_log("-" * 50, "separator")
    agregar_log(
        f"🏁 Finalizado. Total: {contador_enviados} mensajes enviados", "success"
    )
    agregar_log(
        f"📚 Historial total: {len(historial_ips)} IPs únicas contactadas", "info"
    )

    enviando = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/enviar", methods=["POST"])
def enviar_mensaje():
    global enviando

    if enviando:
        return jsonify({"error": "Ya hay un envío en progreso"}), 400

    data = request.json
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({"error": "Debes escribir un mensaje"}), 400

    # Ejecutar en hilo separado
    threading.Thread(target=iniciar_bombardeo, args=(mensaje,), daemon=True).start()

    return jsonify({"success": True, "message": "Envío iniciado"})


@app.route("/api/cancelar", methods=["POST"])
def cancelar():
    global cancelar_envio

    if not enviando:
        return jsonify({"error": "No hay ningún envío en progreso"}), 400

    cancelar_envio = True
    agregar_log("⚠️ Solicitando cancelación...", "info")

    return jsonify({"success": True, "message": "Cancelación solicitada"})


@app.route("/api/estadisticas")
def estadisticas():
    return jsonify(
        {
            "contador": contador_enviados,
            "historial_total": len(historial_ips),
            "enviando": enviando,
        }
    )


@app.route("/api/stream")
def stream():
    """Server-Sent Events para actualizaciones en tiempo real"""

    def event_stream():
        while True:
            try:
                # Obtener log de la cola
                log_item = log_queue.get(timeout=1)
                yield f"data: {json.dumps(log_item)}\n\n"
            except queue.Empty:
                # Enviar heartbeat cada segundo
                yield f"data: {json.dumps({'heartbeat': True})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    # Cargar historial al iniciar
    historial_ips = cargar_historial()
    print("🚀 Servidor web iniciado en http://localhost:8080")
    print("📢 Abre tu navegador y ve a esa dirección")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
