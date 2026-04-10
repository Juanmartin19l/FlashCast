import ipaddress
import json
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def cargar_env_local(path_env):
    if not os.path.exists(path_env):
        return

    with open(path_env, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue

            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            if clave and clave not in os.environ:
                os.environ[clave] = valor


cargar_env_local(os.path.join(BASE_DIR, ".env"))

TARGET_PORT = int(os.environ.get("TARGET_PORT", "5000"))
SEND_TIMEOUT = float(os.environ.get("SEND_TIMEOUT", "2.0"))
SEND_MAX_THREADS = int(os.environ.get("SEND_MAX_THREADS", "500"))
MAX_MESSAGE_BYTES = 2048

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

send_lock = threading.Lock()
send_in_progress = False
send_cancel_requested = False
sent_counter = 0
cached_devices = []


class DatabaseClient:
    def __init__(self):
        self.host = os.environ.get("DB_HOST", "localhost")
        self.port = int(os.environ.get("DB_PORT", "5432"))
        self.dbname = os.environ.get("DB_NAME", "flashcast")
        self.user = os.environ.get("DB_USER", "flashcast")
        self.password = os.environ.get("DB_PASSWORD", "")
        self._conn = None

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )
        return self._conn

    def _validate_config(self):
        missing = []
        if not self.host:
            missing.append("DB_HOST")
        if not self.dbname:
            missing.append("DB_NAME")
        if not self.user:
            missing.append("DB_USER")
        if not self.password:
            missing.append("DB_PASSWORD")
        if missing:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")

    def _execute(self, query, params=None, fetch=True):
        self._validate_config()
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
                return cur.rowcount
        except psycopg2.Error:
            conn.rollback()
            raise

    def list_dispositivos(self):
        rows = self._execute(
            "SELECT id, ip, nombre, departamento, fecha_registro, ultima_actualizacion FROM dispositivos ORDER BY id"
        )
        return [dict(row) for row in rows]

    def get_dispositivo(self, dispositivo_id):
        rows = self._execute(
            "SELECT id, ip, nombre, departamento, fecha_registro, ultima_actualizacion FROM dispositivos WHERE id = %s",
            (dispositivo_id,),
        )
        return dict(rows[0]) if rows else None

    def create_dispositivo(self, ip, nombre, departamento=None):
        self._execute(
            "INSERT INTO dispositivos (ip, nombre, departamento) VALUES (%s, %s, %s)",
            (ip, nombre, departamento),
            fetch=False,
        )
        return self.get_dispositivo_by_ip(ip)

    def update_dispositivo(self, dispositivo_id, ip=None, nombre=None, departamento=None):
        fields = []
        values = []
        if ip is not None:
            fields.append("ip = %s")
            values.append(ip)
        if nombre is not None:
            fields.append("nombre = %s")
            values.append(nombre)
        if departamento is not None:
            fields.append("departamento = %s")
            values.append(departamento)

        if not fields:
            return None

        values.append(dispositivo_id)
        query = f"UPDATE dispositivos SET {', '.join(fields)} WHERE id = %s"
        self._execute(query, tuple(values), fetch=False)
        return self.get_dispositivo(dispositivo_id)

    def delete_dispositivo(self, dispositivo_id):
        self._execute(
            "DELETE FROM dispositivos WHERE id = %s", (dispositivo_id,), fetch=False
        )

    def get_dispositivo_by_ip(self, ip):
        rows = self._execute(
            "SELECT id, ip, nombre, departamento, fecha_registro, ultima_actualizacion FROM dispositivos WHERE ip = %s",
            (ip,),
        )
        return dict(rows[0]) if rows else None


database = DatabaseClient()


def validar_ip(valor):
    try:
        ipaddress.ip_address(str(valor).strip())
        return True
    except ValueError:
        return False


def cargar_dispositivos():
    global cached_devices
    cached_devices = database.list_dispositivos()
    return cached_devices


def normalizar_texto(valor):
    return str(valor or "").strip().lower()


def construir_targets(dispositivos, departamento_objetivo=None):
    targets_by_ip = {}
    depto_buscado = normalizar_texto(departamento_objetivo)

    for dispositivo in dispositivos:
        if not isinstance(dispositivo, dict):
            continue

        ip = str(dispositivo.get("ip", "")).strip()
        nombre = str(dispositivo.get("nombre", "")).strip()
        departamento = normalizar_texto(dispositivo.get("departamento"))
        if not ip or not nombre:
            continue

        if depto_buscado and departamento != depto_buscado:
            continue

        if ip not in targets_by_ip:
            targets_by_ip[ip] = {"ip": ip, "hostnames": []}

        if nombre not in targets_by_ip[ip]["hostnames"]:
            targets_by_ip[ip]["hostnames"].append(nombre)

    return list(targets_by_ip.values())


def enviar_a_ip(target, mensaje, request_id):
    global sent_counter, send_cancel_requested

    ip = target["ip"]
    hostnames = target["hostnames"]
    inicio = time.perf_counter()

    if send_cancel_requested:
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
            s.settimeout(SEND_TIMEOUT)
            s.connect((ip, TARGET_PORT))
            s.sendall(mensaje.encode("utf-8"))

            duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
            with send_lock:
                sent_counter += 1

            print(
                json.dumps(
                    {
                        "evento": "SEND_OK",
                        "request_id": request_id,
                        "ip": ip,
                        "hostnames": hostnames,
                        "duracion_ms": duracion_ms,
                    },
                    ensure_ascii=False,
                )
            )

            return {
                "ok": True,
                "ip": ip,
                "hostnames": hostnames,
                "duracion_ms": duracion_ms,
            }
    except Exception as exc:
        duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
        return {
            "ok": False,
            "ip": ip,
            "hostnames": hostnames,
            "duracion_ms": duracion_ms,
            "error": str(exc),
        }


def ejecutar_envio(mensaje, resultado, request_id, departamento_objetivo=None):
    global sent_counter, send_in_progress, send_cancel_requested

    send_in_progress = True
    send_cancel_requested = False
    with send_lock:
        sent_counter = 0

    try:
        dispositivos = cargar_dispositivos()
    except Exception as exc:
        resultado["error"] = f"No se pudo leer la base de datos: {exc}"
        send_in_progress = False
        return

    targets = construir_targets(
        dispositivos=dispositivos,
        departamento_objetivo=departamento_objetivo,
    )
    if not targets:
        if departamento_objetivo:
            resultado["error"] = (
                f"No hay dispositivos en el departamento '{departamento_objetivo}'"
            )
        else:
            resultado["error"] = "No hay dispositivos en la base de datos"
        send_in_progress = False
        return

    with ThreadPoolExecutor(max_workers=SEND_MAX_THREADS) as executor:
        detalles = list(
            executor.map(
                lambda target: enviar_a_ip(target, mensaje, request_id), targets
            )
        )

    errores = [item for item in detalles if not item["ok"]]
    exitos = [item for item in detalles if item["ok"]]

    if send_cancel_requested:
        resultado["error"] = "Envio cancelado"
    elif errores:
        resultado["error"] = f"{len(errores)} fallaron y {len(exitos)} se enviaron"
    else:
        resultado["success"] = True
        resultado["message"] = "Mensaje enviado exitosamente"

    resultado["detalles"] = detalles
    send_in_progress = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/enviar", methods=["POST"])
def enviar_mensaje():
    global send_in_progress

    if send_in_progress:
        return jsonify({"error": "Ya hay un envio en progreso"}), 400

    data = request.json or {}
    mensaje = str(data.get("mensaje", "")).strip()
    archivo = data.get("archivo")
    departamento = str(data.get("departamento", "")).strip()

    if not mensaje:
        return jsonify({"error": "Debes escribir un mensaje"}), 400

    mensaje_bytes = len(mensaje.encode("utf-8"))
    if mensaje_bytes > MAX_MESSAGE_BYTES:
        return (
            jsonify(
                {
                    "error": f"Maximo {MAX_MESSAGE_BYTES} bytes, recibidos {mensaje_bytes}",
                }
            ),
            400,
        )

    payload = {"mensaje": mensaje}
    if archivo:
        payload["archivo"] = archivo

    request_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    resultado = {}
    ejecutar_envio(
        mensaje=json.dumps(payload, ensure_ascii=False),
        resultado=resultado,
        request_id=request_id,
        departamento_objetivo=departamento or None,
    )

    if "error" in resultado:
        return jsonify(
            {"error": resultado["error"], "detalles": resultado.get("detalles", [])}
        ), 400

    return jsonify(
        {
            "success": True,
            "message": resultado.get("message", "Mensaje enviado exitosamente"),
            "request_id": request_id,
            "departamento": departamento or None,
            "detalles": resultado.get("detalles", []),
        }
    )


@app.route("/api/cancelar", methods=["POST"])
def cancelar_envio():
    global send_cancel_requested

    if not send_in_progress:
        return jsonify({"error": "No hay ningun envio en progreso"}), 400

    send_cancel_requested = True
    return jsonify({"success": True, "message": "Cancelacion solicitada"})


@app.route("/api/dispositivos", methods=["GET"])
def listar_dispositivos():
    try:
        return jsonify({"success": True, "data": cargar_dispositivos()})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/departamentos", methods=["GET"])
def listar_departamentos():
    try:
        dispositivos = cargar_dispositivos()
        departamentos = {
            str(item.get("departamento", "")).strip()
            for item in dispositivos
            if isinstance(item, dict) and str(item.get("departamento", "")).strip()
        }
        return jsonify({"success": True, "data": sorted(departamentos, key=str.lower)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/dispositivos/<int:dispositivo_id>", methods=["GET"])
def obtener_dispositivo(dispositivo_id):
    try:
        dispositivo = database.get_dispositivo(dispositivo_id)
        if dispositivo is None:
            return jsonify({"error": "Dispositivo no encontrado"}), 404
        return jsonify({"success": True, "data": dispositivo})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/dispositivos", methods=["POST"])
def crear_dispositivo():
    try:
        data = request.json or {}
        ip = str(data.get("ip", "")).strip()
        nombre = str(data.get("nombre", "")).strip()

        if not ip or not nombre:
            return jsonify({"error": "Los campos ip y nombre son obligatorios"}), 400
        if not validar_ip(ip):
            return jsonify({"error": "IP invalida"}), 400

        existente = database.get_dispositivo_by_ip(ip)
        if existente:
            return jsonify({"error": f"La IP {ip} ya existe"}), 400

        creado = database.create_dispositivo(ip, nombre, data.get("departamento"))
        cargar_dispositivos()
        return jsonify({"success": True, "data": creado}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/dispositivos/<int:dispositivo_id>", methods=["PUT"])
def actualizar_dispositivo(dispositivo_id):
    try:
        data = request.json or {}
        ip = data.get("ip")
        nombre = data.get("nombre")
        departamento = data.get("departamento")

        if ip is not None:
            ip = str(ip).strip()
            if not ip:
                return jsonify({"error": "El campo ip no puede estar vacio"}), 400
            if not validar_ip(ip):
                return jsonify({"error": "IP invalida"}), 400

        if nombre is not None:
            nombre = str(nombre).strip()
            if not nombre:
                return jsonify({"error": "El campo nombre no puede estar vacio"}), 400

        actualizado = database.update_dispositivo(
            dispositivo_id, ip=ip, nombre=nombre, departamento=departamento
        )
        if actualizado is None:
            return jsonify({"error": "Dispositivo no encontrado"}), 404

        cargar_dispositivos()
        return jsonify({"success": True, "data": actualizado})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/dispositivos/<int:dispositivo_id>", methods=["DELETE"])
def eliminar_dispositivo(dispositivo_id):
    try:
        database.delete_dispositivo(dispositivo_id)
        cargar_dispositivos()
        return jsonify({"success": True, "message": "Dispositivo eliminado"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No se envio ningun archivo"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No se selecciono ningun archivo"}), 400

    if not secure_filename(file.filename or ""):
        return jsonify({"error": "Nombre de archivo invalido"}), 400

    filename = secure_filename(file.filename or "")
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)
    return jsonify({"success": True, "filename": filename, "message": "Archivo subido"})


@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file(filename):
    if not secure_filename(filename):
        return jsonify({"error": "Nombre de archivo invalido"}), 400

    try:
        return send_from_directory(
            app.config["UPLOAD_FOLDER"], filename, as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado"}), 404


@app.route("/api/estadisticas")
def estadisticas():
    return jsonify(
        {
            "contador": sent_counter,
            "historial_total": len(cached_devices),
            "enviando": send_in_progress,
        }
    )


if __name__ == "__main__":
    try:
        cargar_dispositivos()
    except Exception as exc:
        print(f"No se pudo conectar a la base de datos al iniciar: {exc}")

    print("Servidor iniciado en http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)