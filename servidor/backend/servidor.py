import socket
from concurrent.futures import ThreadPoolExecutor
import json
import os
from flask import Flask, render_template, request, jsonify, Response
import threading
import queue
import time

# --- CONFIGURACIÓN ---
PUERTO = 5000
TIMEOUT = 2.0  # Segundos de espera para conexión
MAX_HILOS = 500
ARCHIVO_MAQUINAS = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "machines.json"
)
MAX_CARACTERES = 2048  # Límite de caracteres del mensaje

# Configurar Flask para usar las carpetas del frontend
app = Flask(
    __name__,
    template_folder=os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "templates"
    ),
    static_folder=os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "static"
    ),
)

# Variables globales
log_queue = queue.Queue()
contador_enviados = 0
maquinas_cache = {}  # Cache del archivo machines.json
lock = threading.Lock()
enviando = False
cancelar_envio = False


def cargar_maquinas():
    """Carga la lista de máquinas desde machines.json"""
    if os.path.exists(ARCHIVO_MAQUINAS):
        try:
            with open(ARCHIVO_MAQUINAS, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error cargando machines.json: {e}")
            return {}
    return {}


def agregar_log(texto, tipo="info"):
    """Agrega una línea al log"""
    log_queue.put({"texto": texto, "tipo": tipo, "timestamp": time.time()})


def enviar_a_ip(ip, mensaje):
    global contador_enviados, cancelar_envio

    if cancelar_envio:
        return False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((str(ip), PUERTO))
            s.sendall(mensaje.encode("utf-8"))

            with lock:
                contador_enviados += 1
                agregar_log(f"✅ {ip}", "nueva")

            return True
    except socket.timeout:
        agregar_log(f"⏱️ {ip} - timeout", "error")
    except ConnectionRefusedError:
        agregar_log(f"🚫 {ip} - cliente no ejecutándose", "error")
    except OSError as e:
        agregar_log(f"❌ {ip} - {e}", "error")
    return False


def iniciar_bombardeo(mensaje):
    global contador_enviados, enviando, cancelar_envio, maquinas_cache

    enviando = True
    cancelar_envio = False

    with lock:
        contador_enviados = 0

    agregar_log("🚀 Iniciando envío masivo...", "info")

    # Recargar machines.json (puede haber sido actualizado por discovery_service)
    maquinas_cache = cargar_maquinas()

    # Extraer IPs del JSON
    ips = []
    for hostname, data in maquinas_cache.items():
        if isinstance(data, dict) and "ip" in data:
            ips.append(data["ip"])
        elif isinstance(data, str):
            ips.append(data)

    if not ips:
        agregar_log("⚠️ No hay máquinas en machines.json", "error")
        agregar_log("💡 Ejecuta discovery_service.py para encontrar máquinas", "info")
        enviando = False
        return

    agregar_log(f"📤 Enviando a {len(ips)} máquinas...", "info")

    with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
        list(executor.map(lambda ip: enviar_a_ip(ip, mensaje), ips))

    if cancelar_envio:
        agregar_log("🛑 Envío cancelado", "error")
    else:
        agregar_log(f"🏁 Finalizado. {contador_enviados} mensajes enviados", "success")

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

    # Validar longitud del mensaje en bytes (UTF-8)
    mensaje_bytes = len(mensaje.encode("utf-8"))
    if mensaje_bytes > MAX_CARACTERES:
        return (
            jsonify(
                {
                    "error": f"El mensaje es demasiado largo. Máximo {MAX_CARACTERES} bytes. Tu mensaje tiene {mensaje_bytes} bytes."
                }
            ),
            400,
        )

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
            "historial_total": len(maquinas_cache),
            "enviando": enviando,
        }
    )


@app.route("/api/stream")
def stream():
    """Server-Sent Events para actualizaciones en tiempo real"""

    def event_stream():
        contador_heartbeat = 0
        while True:
            try:
                # Obtener log de la cola
                log_item = log_queue.get(timeout=1)
                yield f"data: {json.dumps(log_item)}\n\n"
                contador_heartbeat = 0
            except queue.Empty:
                # Enviar estadísticas cada 2 segundos (en lugar de solo heartbeat)
                contador_heartbeat += 1
                if contador_heartbeat >= 2:
                    stats = {
                        "type": "estadisticas",
                        "contador": contador_enviados,
                        "historial_total": len(maquinas_cache),
                        "enviando": enviando,
                    }
                    yield f"data: {json.dumps(stats)}\n\n"
                    contador_heartbeat = 0
                else:
                    # Enviar heartbeat
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    # Cargar máquinas al iniciar
    maquinas_cache = cargar_maquinas()
    print("🚀 Servidor web iniciado en http://localhost:8080")
    print("📢 Abre tu navegador y ve a esa dirección")
    print("💡 Asegúrate de ejecutar discovery_service.py para actualizar machines.json")
    print(f"📚 Máquinas cargadas: {len(maquinas_cache)}")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
