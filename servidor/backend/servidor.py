import socket
from concurrent.futures import ThreadPoolExecutor
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import threading
import queue
import time
from werkzeug.utils import secure_filename

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

# Carpeta para subir documentos
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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


def log_event(evento, **kwargs):
    """Log estructurado para stdout (visible en docker logs)."""
    payload = {
        "evento": evento,
        "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
    }
    payload.update(kwargs)
    print(f"[{evento}] {json.dumps(payload, ensure_ascii=False)}")


def allowed_file(filename):
    return bool(filename and secure_filename(filename))


def construir_targets(maquinas):
    """
    Construye una lista de destinos únicos por IP.
    Cada destino conserva uno o más hostnames asociados.
    """
    targets_by_ip = {}

    for hostname, data in maquinas.items():
        ip = None
        if isinstance(data, dict):
            ip = data.get("ip")
        elif isinstance(data, str):
            ip = data

        if not ip:
            continue

        ip = str(ip).strip()
        if not ip:
            continue

        if ip not in targets_by_ip:
            targets_by_ip[ip] = {"ip": ip, "hostnames": []}

        if hostname not in targets_by_ip[ip]["hostnames"]:
            targets_by_ip[ip]["hostnames"].append(hostname)

    return list(targets_by_ip.values())


def enviar_a_ip(target, mensaje, request_id):
    global contador_enviados, cancelar_envio

    ip = target["ip"]
    hostnames = target["hostnames"]
    inicio = time.perf_counter()

    if cancelar_envio:
        return {
            "ok": False,
            "ip": ip,
            "hostnames": hostnames,
            "estado": "cancelado",
            "duracion_ms": 0,
            "error": "Cancelado antes del intento",
        }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((str(ip), PUERTO))
            s.sendall(mensaje.encode("utf-8"))

            duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
            with lock:
                contador_enviados += 1
            log_event(
                "SEND_OK",
                request_id=request_id,
                ip=ip,
                hostnames=hostnames,
                puerto=PUERTO,
                duracion_ms=duracion_ms,
                bytes_enviados=len(mensaje.encode("utf-8")),
            )
            return {
                "ok": True,
                "ip": ip,
                "hostnames": hostnames,
                "duracion_ms": duracion_ms,
            }
    except Exception as e:
        duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
        log_event(
            "SEND_ERROR",
            request_id=request_id,
            ip=ip,
            hostnames=hostnames,
            puerto=PUERTO,
            duracion_ms=duracion_ms,
            error=str(e),
        )
        return {
            "ok": False,
            "ip": ip,
            "hostnames": hostnames,
            "duracion_ms": duracion_ms,
            "error": str(e),
        }


def iniciar_bombardeo(mensaje, resultado, request_id):
    global contador_enviados, enviando, cancelar_envio, maquinas_cache

    inicio_envio = time.perf_counter()
    enviando = True
    cancelar_envio = False

    with lock:
        contador_enviados = 0

    maquinas_cache = cargar_maquinas()
    targets = construir_targets(maquinas_cache)

    if not targets:
        resultado["error"] = "No hay máquinas en machines.json"
        enviando = False
        return

    log_event(
        "SEND_START",
        request_id=request_id,
        total_destinos=len(targets),
        timeout_segundos=TIMEOUT,
        puerto_destino=PUERTO,
    )

    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
        resultados = list(
            executor.map(lambda target: enviar_a_ip(target, mensaje, request_id), targets)
        )

    errores = [r for r in resultados if not r["ok"]]
    exitos = [r for r in resultados if r["ok"]]
    duracion_total_ms = round((time.perf_counter() - inicio_envio) * 1000, 2)

    if cancelar_envio:
        resultado["error"] = "Envío cancelado"
    elif errores:
        resultado["error"] = (
            f"{len(errores)} clientes tuvieron error y {len(exitos)} recibieron OK"
        )
    else:
        resultado["success"] = True
        resultado["message"] = "Mensaje enviado exitosamente"

    resultado["detalles"] = resultados
    log_event(
        "SEND_SUMMARY",
        request_id=request_id,
        total=len(resultados),
        exitos=len(exitos),
        errores=len(errores),
        cancelado=cancelar_envio,
        duracion_total_ms=duracion_total_ms,
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
    archivo = data.get("archivo")
    request_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    log_event(
        "SEND_REQUEST",
        request_id=request_id,
        client_ip=request.remote_addr,
        archivo=archivo,
        mensaje_bytes=len(mensaje.encode("utf-8")),
    )

    if not mensaje:
        return jsonify({"error": "Debes escribir un mensaje"}), 400

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

    mensaje_envio = json.dumps({"mensaje": mensaje, "archivo": archivo} if archivo else {"mensaje": mensaje}, ensure_ascii=False)
    log_event("SEND_PAYLOAD_READY", request_id=request_id, mensaje_preview=mensaje[:120])

    resultado = {}
    thread = threading.Thread(
        target=iniciar_bombardeo,
        args=(mensaje_envio, resultado, request_id),
        daemon=True,
    )
    thread.start()
    thread.join()  # Esperar a que termine para responder con el resultado

    if "error" in resultado:
        return (
            jsonify(
                {
                    "error": resultado["error"],
                    "request_id": request_id,
                    "detalles": resultado.get("detalles", []),
                }
            ),
            400,
        )
    return jsonify(
        {
            "success": True,
            "message": resultado.get("message", "Mensaje enviado exitosamente"),
            "request_id": request_id,
            "detalles": resultado.get("detalles", []),
        }
    )


@app.route("/api/cancelar", methods=["POST"])
def cancelar():
    global cancelar_envio

    if not enviando:
        return jsonify({"error": "No hay ningún envío en progreso"}), 400

    cancelar_envio = True
    agregar_log("Solicitando cancelación...", "info")

    return jsonify({"success": True, "message": "Cancelación solicitada"})


@app.route("/api/machines", methods=["GET"])
def obtener_machines():
    """Obtiene el contenido de machines.json"""
    maquinas = cargar_maquinas()
    return jsonify(maquinas)


@app.route("/api/machines", methods=["POST"])
def guardar_machines():
    """Guarda el contenido de machines.json"""
    try:
        data = request.json

        # Validar que sea un diccionario
        if not isinstance(data, dict):
            return jsonify({"error": "El contenido debe ser un objeto JSON"}), 400

        # Guardar en archivo
        os.makedirs(os.path.dirname(ARCHIVO_MAQUINAS), exist_ok=True)
        with open(ARCHIVO_MAQUINAS, "w") as f:
            json.dump(data, f, indent=2)

        # Actualizar cache
        global maquinas_cache
        maquinas_cache = data

        agregar_log(f"Machines.json actualizado con {len(data)} máquinas", "success")

        return jsonify(
            {"success": True, "message": f"Se guardaron {len(data)} máquinas"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        agregar_log(f"Archivo subido: {filename}", "success")
        return jsonify({"success": True, "filename": filename, "message": "Archivo subido correctamente"})
    else:
        return jsonify({"error": "Nombre de archivo inválido"}), 400


@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):
    # Validar que el nombre sea seguro antes de servir el archivo
    if not allowed_file(filename):
        return jsonify({"error": "Nombre de archivo inválido"}), 400
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado"}), 404


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
    print(
        "💡 Ejecuta discovery_service.py en tu máquina local para actualizar machines.json"
    )
    print(f"📚 Máquinas cargadas: {len(maquinas_cache)}")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
