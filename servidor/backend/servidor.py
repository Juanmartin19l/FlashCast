import ipaddress
import json
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
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


class NocoDBClient:
    def __init__(self):
        self.base_url = os.environ.get("NOCODB_BASE_URL", "").rstrip("/")
        self.api_token = os.environ.get("NOCODB_API_TOKEN", "")
        self.org = os.environ.get("NOCODB_ORG", "noco")
        self.project = os.environ.get("NOCODB_PROJECT", "nc")
        self.table = os.environ.get("NOCODB_TABLE", "dispositivos")
        self.api_mode = os.environ.get("NOCODB_API_MODE", "auto").strip().lower()
        self.request_timeout = int(os.environ.get("NOCODB_TIMEOUT", "10"))

    def _headers(self):
        return {"xc-token": self.api_token, "Content-Type": "application/json"}

    def _v1_table_url(self):
        return (
            f"{self.base_url}/api/v1/db/data/v1/{self.org}/{self.project}/{self.table}"
        )

    def _v2_table_url(self):
        return f"{self.base_url}/api/v2/tables/{self.table}/records"

    def _validate_config(self):
        missing = []
        if not self.base_url:
            missing.append("NOCODB_BASE_URL")
        if not self.api_token:
            missing.append("NOCODB_API_TOKEN")
        if missing:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")

    def _do_request(self, base_url, method, path="", payload=None, params=None):
        url = base_url
        if path:
            url = f"{url}/{path}"

        response = requests.request(
            method=method,
            url=url,
            headers=self._headers(),
            json=payload,
            params=params,
            timeout=self.request_timeout,
        )

        try:
            body = response.json()
        except ValueError:
            body = {"error": response.text}

        return response.status_code, body, url

    def _request(self, method, path="", payload=None, params=None):
        self._validate_config()

        if self.api_mode not in {"auto", "v1", "v2"}:
            raise ValueError("NOCODB_API_MODE invalido. Usa: auto, v1 o v2")

        if self.api_mode == "v1":
            endpoints = [("v1", self._v1_table_url())]
        elif self.api_mode == "v2":
            endpoints = [("v2", self._v2_table_url())]
        else:
            endpoints = [
                ("v1", self._v1_table_url()),
                ("v2", self._v2_table_url()),
            ]

        last_error = None
        for version, base_url in endpoints:
            status_code, body, final_url = self._do_request(
                base_url=base_url,
                method=method,
                path=path,
                payload=payload,
                params=params,
            )

            if status_code < 400:
                return body

            msg = (
                body.get("msg") or body.get("message") or body.get("error") or str(body)
            )
            last_error = (
                f"NocoDB {version} devolvio {status_code}: {msg} (URL: {final_url})"
            )

            if self.api_mode != "auto":
                break

        raise RuntimeError(last_error or "Error desconocido consultando NocoDB")

    def list_dispositivos(self):
        body = self._request("GET", params={"limit": 1000})
        if isinstance(body, dict) and "list" in body:
            return body["list"]
        if isinstance(body, list):
            return body
        return []

    def get_dispositivo(self, dispositivo_id):
        return self._request("GET", path=dispositivo_id)

    def create_dispositivo(self, payload):
        return self._request("POST", payload=payload)

    def update_dispositivo(self, dispositivo_id, payload):
        return self._request("PATCH", path=dispositivo_id, payload=payload)

    def delete_dispositivo(self, dispositivo_id):
        return self._request("DELETE", path=dispositivo_id)


nocodb = NocoDBClient()


def validar_ip(valor):
    try:
        ipaddress.ip_address(str(valor).strip())
        return True
    except ValueError:
        return False


def cargar_dispositivos():
    global cached_devices
    cached_devices = nocodb.list_dispositivos()
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
        resultado["error"] = f"No se pudo leer NocoDB: {exc}"
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
            resultado["error"] = "No hay dispositivos en NocoDB"
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


@app.route("/api/dispositivos/<dispositivo_id>", methods=["GET"])
def obtener_dispositivo(dispositivo_id):
    try:
        return jsonify(
            {"success": True, "data": nocodb.get_dispositivo(dispositivo_id)}
        )
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

        payload = {
            "ip": ip,
            "nombre": nombre,
            "departamento": data.get("departamento"),
        }
        creado = nocodb.create_dispositivo(payload)
        cargar_dispositivos()
        return jsonify({"success": True, "data": creado}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/dispositivos/<dispositivo_id>", methods=["PUT"])
def actualizar_dispositivo(dispositivo_id):
    try:
        data = request.json or {}
        payload = {}

        if "ip" in data:
            ip = str(data.get("ip", "")).strip()
            if not ip:
                return jsonify({"error": "El campo ip no puede estar vacio"}), 400
            if not validar_ip(ip):
                return jsonify({"error": "IP invalida"}), 400
            payload["ip"] = ip

        if "nombre" in data:
            nombre = str(data.get("nombre", "")).strip()
            if not nombre:
                return jsonify({"error": "El campo nombre no puede estar vacio"}), 400
            payload["nombre"] = nombre

        if "departamento" in data:
            payload["departamento"] = data.get("departamento")

        if not payload:
            return jsonify({"error": "No se enviaron campos para actualizar"}), 400

        actualizado = nocodb.update_dispositivo(dispositivo_id, payload)
        cargar_dispositivos()
        return jsonify({"success": True, "data": actualizado})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/api/dispositivos/<dispositivo_id>", methods=["DELETE"])
def eliminar_dispositivo(dispositivo_id):
    try:
        nocodb.delete_dispositivo(dispositivo_id)
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


@app.route("/api/download/<filename>", methods=["GET"])
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
        print(f"No se pudo conectar a NocoDB al iniciar: {exc}")

    print("Servidor iniciado en http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
