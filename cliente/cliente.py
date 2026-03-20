import socket
import tkinter as tk
from tkinter import filedialog, font, messagebox
import logging
import threading
import signal
import sys
import os
import subprocess
import locale
from datetime import datetime
import requests
import json
import queue
from urllib.parse import quote


def obtener_directorio_base():
    """Devuelve un directorio estable para archivos locales del cliente."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# Configuración de logging
def configurar_logging():
    """Configura el sistema de logging para producción"""
    try:
        log_dir = os.path.join(obtener_directorio_base(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"esclavo_{datetime.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar logging: {e}")
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)


logger = configurar_logging()

# Configuración global (hardcodeada)
CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "BACKEND_PORT": 8080,
    "TIMEOUT": 30,
    "MAX_BUFFER": 8192,
    "CONFIRMATION_WORD": "CONFIRMAR",
    "PROCESO_BLOQUEANTE": "MacroRecorder.exe",
}

server_running = True
server_socket = None
app_root = None
notification_queue = queue.Queue()


def proceso_esta_abierto(nombre_proceso):
    """Verifica si un proceso está abierto usando tasklist"""
    try:
        resultado = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {nombre_proceso}"],
            capture_output=True,
            text=False,
            timeout=5,
        )

        codificacion = locale.getpreferredencoding(False) or "cp1252"
        salida = (resultado.stdout or b"").decode(codificacion, errors="replace")

        # Si el proceso está en la lista, tasklist lo retorna
        return nombre_proceso.lower() in salida.lower()
    except Exception as e:
        logger.error(f"Error verificando proceso {nombre_proceso}: {e}")
        return False


def mostrar_alerta(parent_root, mensaje, archivo_nombre=None, servidor_host=None):
    root = tk.Toplevel(parent_root)
    root.overrideredirect(True)

    # Colores corporativos - Celeste
    COLOR_PRIMARIO = "#0ea5e9"
    COLOR_PRIMARIO_CLARO = "#e0f2fe"
    COLOR_FONDO = "#fafafa"
    COLOR_TEXTO = "#1f2937"
    COLOR_TEXTO_SECUNDARIO = "#6b7280"
    COLOR_BORDE = "#e5e7eb"
    COLOR_ERROR = "#ef4444"
    COLOR_BLANCO = "#FFFFFF"

    root.attributes("-topmost", True)
    root.configure(bg=COLOR_FONDO)

    # Centrar ventana
    ancho_ventana = 720
    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()
    alto_ventana = min(600, max(420, alto_pantalla - 80))
    x = (ancho_pantalla - ancho_ventana) // 2
    y = (alto_pantalla - alto_ventana) // 2

    root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
    root.resizable(False, False)

    scroll_container = tk.Frame(root, bg=COLOR_FONDO)
    scroll_container.pack(fill=tk.BOTH, expand=True)

    outer_canvas = tk.Canvas(scroll_container, bg=COLOR_FONDO, highlightthickness=0)
    outer_scrollbar = tk.Scrollbar(
        scroll_container, orient="vertical", command=outer_canvas.yview
    )
    outer_canvas.configure(yscrollcommand=outer_scrollbar.set)

    outer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Frame principal con padding
    main_frame = tk.Frame(outer_canvas, bg=COLOR_FONDO)
    main_window = outer_canvas.create_window((0, 0), window=main_frame, anchor="nw")
    main_frame.configure(padx=28, pady=24)

    def actualizar_scroll_principal(event=None):
        outer_canvas.configure(scrollregion=outer_canvas.bbox("all"))

    def ajustar_ancho_principal(event):
        outer_canvas.itemconfigure(main_window, width=event.width)

    def on_outer_mousewheel(event):
        region = outer_canvas.bbox("all")
        if region and (region[3] - region[1]) > outer_canvas.winfo_height():
            outer_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    main_frame.bind("<Configure>", actualizar_scroll_principal)
    outer_canvas.bind("<Configure>", ajustar_ancho_principal)
    root.bind("<MouseWheel>", on_outer_mousewheel)

    # Banner "Notificación Importante"
    banner = tk.Label(
        main_frame,
        text="NOTIFICACIÓN IMPORTANTE",
        font=font.Font(family="Segoe UI", size=10, weight="bold"),
        fg=COLOR_PRIMARIO,
        bg=COLOR_PRIMARIO_CLARO,
        anchor="w",
        padx=14,
        pady=12,
    )
    banner.pack(fill=tk.X, pady=(0, 12))

    # Contenedor visual del mensaje dentro del contenedor principal.
    mensaje_frame = tk.Frame(
        main_frame,
        bg=COLOR_BLANCO,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
    )
    mensaje_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

    # El widget Text no maneja scroll propio; toda la rueda va al contenedor externo.
    mensaje_text = tk.Text(
        mensaje_frame,
        font=font.Font(family="Segoe UI", size=14),
        fg=COLOR_TEXTO,
        bg=COLOR_BLANCO,
        wrap=tk.WORD,
        padx=24,
        pady=24,
        state="disabled",
        width=70,
        relief=tk.FLAT,
        borderwidth=0,
        height=10,
        takefocus=0,
        cursor="arrow",
    )
    mensaje_text.pack(fill=tk.BOTH, expand=True)

    def on_text_mousewheel(event):
        on_outer_mousewheel(event)
        return "break"

    mensaje_text.bind("<MouseWheel>", on_text_mousewheel)

    # Configurar tags para formato
    mensaje_text.tag_config(
        "h1",
        font=font.Font(family="Segoe UI", size=22, weight="bold"),
        spacing3=12,
        foreground="#111827",
    )
    mensaje_text.tag_config(
        "h2",
        font=font.Font(family="Segoe UI", size=18, weight="bold"),
        spacing3=10,
        foreground="#1f2937",
    )
    mensaje_text.tag_config(
        "bold", font=font.Font(family="Segoe UI", size=14, weight="bold")
    )

    # Función para procesar y mostrar markdown simplificado
    def mostrar_markdown(texto):
        mensaje_text.config(state="normal")
        mensaje_text.delete("1.0", tk.END)

        lineas = texto.split("\n")
        for linea in lineas:
            # Encabezados H1
            if linea.startswith("# "):
                mensaje_text.insert(tk.END, linea[2:] + "\n", "h1")
            # Encabezados H2
            elif linea.startswith("## "):
                mensaje_text.insert(tk.END, linea[3:] + "\n", "h2")
            # Línea normal con negritas
            else:
                procesar_linea_con_negritas(linea + "\n")

        mensaje_text.config(state="disabled")

        # Ajustar la altura del Text al contenido para usar solo el scroll externo.
        lineas_visibles = int(mensaje_text.count("1.0", "end", "displaylines")[0])
        mensaje_text.configure(height=max(10, lineas_visibles))

    def procesar_linea_con_negritas(linea):
        """
        Procesar **negritas** de forma simple y robusta.
        Solo busca ** ** sin otros formatos.
        """
        pos = 0

        while pos < len(linea):
            # Buscar el próximo **
            inicio_bold = linea.find("**", pos)

            if inicio_bold == -1:
                # No hay más negritas, insertar el resto
                if pos < len(linea):
                    mensaje_text.insert(tk.END, linea[pos:])
                break

            # Insertar texto antes de **
            if inicio_bold > pos:
                mensaje_text.insert(tk.END, linea[pos:inicio_bold])

            # Buscar el cierre de **
            fin_bold = linea.find("**", inicio_bold + 2)

            if fin_bold == -1:
                # No hay cierre, insertar ** como texto literal y el resto
                mensaje_text.insert(tk.END, linea[inicio_bold:])
                break
            else:
                # Extraer contenido entre **
                contenido_bold = linea[inicio_bold + 2 : fin_bold]
                mensaje_text.insert(tk.END, contenido_bold, "bold")
                pos = fin_bold + 2

    # Mostrar el mensaje con formato Markdown
    mostrar_markdown(mensaje)

    # Separador
    separator = tk.Frame(main_frame, height=1, bg=COLOR_BORDE)
    separator.pack(fill=tk.X, pady=4)

    if archivo_nombre:
        archivo_frame = tk.Frame(main_frame, bg=COLOR_PRIMARIO_CLARO)
        archivo_frame.pack(fill=tk.X, pady=(8, 12))

        tk.Label(
            archivo_frame,
            text="ARCHIVO DISPONIBLE PARA DESCARGAR",
            font=font.Font(family="Segoe UI", size=10, weight="bold"),
            fg=COLOR_PRIMARIO,
            bg=COLOR_PRIMARIO_CLARO,
            anchor="w",
            padx=14,
            pady=8,
        ).pack(fill=tk.X)

        tk.Label(
            archivo_frame,
            text=archivo_nombre,
            font=font.Font(family="Segoe UI", size=11, weight="bold"),
            fg=COLOR_TEXTO,
            bg=COLOR_PRIMARIO_CLARO,
            anchor="w",
            padx=14,
        ).pack(fill=tk.X)

        estado_descarga = tk.StringVar(
            value="El archivo se descargará cuando confirme el mensaje."
        )

        tk.Label(
            archivo_frame,
            textvariable=estado_descarga,
            font=font.Font(family="Segoe UI", size=9),
            fg=COLOR_TEXTO_SECUNDARIO,
            bg=COLOR_PRIMARIO_CLARO,
            anchor="w",
            justify=tk.LEFT,
            padx=14,
        ).pack(fill=tk.X, pady=(4, 8))

    # Instrucciones
    instruccion_frame = tk.Frame(main_frame, bg=COLOR_FONDO)
    instruccion_frame.pack(fill=tk.X, pady=(8, 12))

    tk.Label(
        instruccion_frame,
        text='Escriba "CONFIRMAR" para cerrar.',
        font=font.Font(family="Segoe UI", size=10),
        fg=COLOR_TEXTO_SECUNDARIO,
        bg=COLOR_FONDO,
        anchor="w",
        justify=tk.LEFT,
    ).pack(fill=tk.X)

    if archivo_nombre:
        tk.Label(
            instruccion_frame,
            text="Al confirmar, se solicitará una carpeta para descargar el adjunto.",
            font=font.Font(family="Segoe UI", size=10),
            fg=COLOR_TEXTO_SECUNDARIO,
            bg=COLOR_FONDO,
            anchor="w",
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(4, 0))

    # Frame para campo de texto y botón (en la misma línea)
    input_frame = tk.Frame(main_frame, bg=COLOR_FONDO)
    input_frame.pack(fill=tk.X, pady=(0, 8))

    # Campo de texto con borde
    entry_frame = tk.Frame(input_frame, bg=COLOR_BORDE, bd=0)
    entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

    entry = tk.Entry(
        entry_frame,
        font=font.Font(family="Segoe UI", size=11),
        relief=tk.FLAT,
        bg=COLOR_BLANCO,
        fg=COLOR_TEXTO,
        insertbackground=COLOR_PRIMARIO,
    )
    entry.pack(fill=tk.X, padx=1, pady=1, ipady=10)

    # Función para convertir a mayúsculas mientras se escribe
    def a_mayusculas(*args):
        texto = entry_var.get().upper()
        entry_var.set(texto)

    entry_var = tk.StringVar()
    entry_var.trace("w", a_mayusculas)
    entry.config(textvariable=entry_var)
    entry.focus_set()

    def verificar_confirmacion(event=None):
        texto = entry.get().strip().upper()
        if texto == CONFIG["CONFIRMATION_WORD"]:
            if archivo_nombre:
                carpeta_destino = filedialog.askdirectory(
                    parent=root,
                    title="Seleccionar carpeta de descarga",
                    mustexist=True,
                )

                if not carpeta_destino:
                    estado_descarga.set("Debe seleccionar una carpeta para descargar el archivo adjunto.")
                    error_label.config(text="Seleccione una carpeta válida para continuar.")
                    root.after(5000, lambda: error_label.config(text=""))
                    return

                estado_descarga.set("Descargando archivo adjunto...")
                ruta_descargada = descargar_documento(
                    archivo_nombre,
                    servidor_host=servidor_host,
                    puerto_backend=CONFIG["BACKEND_PORT"],
                    carpeta_destino=carpeta_destino,
                )

                if not ruta_descargada:
                    estado_descarga.set("No se pudo descargar el archivo. Revise la conexión con el servidor.")
                    error_label.config(text="Ocurrió un error al descargar el archivo adjunto.")
                    root.after(5000, lambda: error_label.config(text=""))
                    return

                estado_descarga.set(f"Archivo descargado en: {ruta_descargada}")
                archivo_abierto = abrir_archivo_descargado(ruta_descargada)

                if archivo_abierto:
                    messagebox.showinfo(
                        "Descarga completada",
                        f"El archivo se descargó y abrió correctamente:\n{ruta_descargada}",
                        parent=root,
                    )
                else:
                    messagebox.showwarning(
                        "Descarga completada",
                        f"El archivo se descargó correctamente, pero no se pudo abrir automáticamente:\n{ruta_descargada}",
                        parent=root,
                    )

            logger.info("Confirmación exitosa por usuario")
            root.destroy()
        else:
            error_label.config(
                text=f'La palabra debe coincidir con "{CONFIG["CONFIRMATION_WORD"]}" exactamente'
            )
            entry.delete(0, tk.END)
            logger.warning(f"Intento fallido de confirmación: {texto}")
            # Limpiar el mensaje de error después de 5 segundos
            root.after(5000, lambda: error_label.config(text=""))

    boton = tk.Button(
        input_frame,
        text="Confirmar",
        command=verificar_confirmacion,
        font=font.Font(family="Segoe UI", size=11, weight="bold"),
        bg=COLOR_PRIMARIO,
        fg=COLOR_BLANCO,
        padx=24,
        pady=10,
        cursor="hand2",
        activebackground="#38bdf8",
        relief=tk.FLAT,
        borderwidth=0,
    )
    boton.pack(side=tk.RIGHT)
    boton.bind("<Return>", lambda e: verificar_confirmacion())

    # Mensaje de error
    error_label = tk.Label(
        main_frame,
        text="",
        font=font.Font(family="Segoe UI", size=9),
        fg=COLOR_ERROR,
        bg=COLOR_FONDO,
        anchor="w",
    )
    error_label.pack(fill=tk.X, pady=(0, 4))

    # Nota de contacto
    nota_contacto = tk.Label(
        main_frame,
        text="Cualquier consulta comunicarse con el departamento de coordinación",
        font=font.Font(family="Segoe UI", size=9, slant="italic"),
        fg="#9ca3af",
        bg=COLOR_FONDO,
    )
    nota_contacto.pack(pady=0)

    # Permitir Enter para confirmar
    entry.bind("<Return>", verificar_confirmacion)

    # Cerrar automáticamente después de 2 horas (7200000 ms)
    def cierre_automatico():
        logger.info("Cierre automático por tiempo límite (2 horas)")
        root.destroy()

    root.after(7200000, cierre_automatico)

    # Deshabilitar cierre no autorizado
    root.protocol("WM_DELETE_WINDOW", lambda: None)


def encolar_alerta(mensaje, archivo_nombre=None, servidor_host=None):
    """Encola una alerta para ser mostrada en el hilo principal."""
    notification_queue.put(
        {
            "mensaje": mensaje,
            "archivo_nombre": archivo_nombre,
            "servidor_host": servidor_host,
        }
    )


def procesar_alertas():
    """Procesa alertas pendientes desde el hilo principal de Tkinter."""
    global app_root

    if app_root is None:
        return

    try:
        while True:
            alerta = notification_queue.get_nowait()
            mostrar_alerta(
                app_root,
                alerta["mensaje"],
                archivo_nombre=alerta.get("archivo_nombre"),
                servidor_host=alerta.get("servidor_host"),
            )
    except queue.Empty:
        pass

    if server_running:
        app_root.after(200, procesar_alertas)


def iniciar_cliente():
    """Inicia el servidor para escuchar mensajes entrantes"""
    global server_running, server_socket

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(CONFIG["TIMEOUT"])

        server_socket.bind((CONFIG["HOST"], CONFIG["PORT"]))
        server_socket.listen(5)

        logger.info(f"Servidor iniciado en {CONFIG['HOST']}:{CONFIG['PORT']}")

        while server_running:
            try:
                conn, addr = server_socket.accept()
                conn.settimeout(CONFIG["TIMEOUT"])

                logger.info(f"Conexión aceptada desde {addr}")

                try:
                    datos = conn.recv(CONFIG["MAX_BUFFER"])

                    if not datos:
                        logger.warning(f"Conexión vacía desde {addr}")
                        conn.close()
                        continue

                    mensaje = datos.decode("utf-8", errors="replace").strip()

                    if not mensaje:
                        logger.warning(f"Mensaje vacío desde {addr}")
                        conn.close()
                        continue

                    logger.info(
                        f"Mensaje recibido de {addr}: {len(mensaje)} caracteres"
                    )
                    print(f"[DEBUG] Mensaje recibido del servidor: {mensaje}")

                    # Verificar si el proceso bloqueante está abierto
                    if proceso_esta_abierto(CONFIG["PROCESO_BLOQUEANTE"]):
                        logger.warning(
                            f"Proceso {CONFIG['PROCESO_BLOQUEANTE']} está activo. Mensaje DESCARTADO."
                        )
                        # No se encola ni se muestra el mensaje
                    else:
                        # Verificar si el mensaje contiene información de archivo adjunto
                        archivo_nombre = None
                        if mensaje.startswith('{') and mensaje.endswith('}'):  # JSON
                            try:
                                data_msg = json.loads(mensaje)
                                mensaje_texto = data_msg.get('mensaje', '')
                                archivo_nombre = data_msg.get('archivo')
                            except Exception as e:
                                logger.error(f"Error decodificando JSON recibido: {e}")
                                mensaje_texto = mensaje
                        else:
                            mensaje_texto = mensaje

                        encolar_alerta(mensaje_texto, archivo_nombre, addr[0])

                except socket.timeout:
                    logger.error(f"Timeout en recepción de datos desde {addr}")
                except Exception as e:
                    logger.error(f"Error procesando mensaje de {addr}: {e}")
                finally:
                    try:
                        conn.close()
                    except (OSError, Exception) as e:
                        logger.debug(f"Error cerrando conexión: {e}")

            except socket.timeout:
                continue
            except Exception as e:
                if server_running:
                    logger.error(f"Error aceptando conexión: {e}")

    except OSError as e:
        logger.error(f"Error al iniciar servidor: {e}")
        logger.error(f"Verifica que el puerto {CONFIG['PORT']} esté disponible")
    except Exception as e:
        logger.error(f"Error inesperado en servidor: {e}")
    finally:
        server_running = False
        if server_socket:
            try:
                server_socket.close()
                logger.info("Servidor cerrado correctamente")
            except (OSError, Exception) as e:
                logger.debug(f"Error cerrando socket: {e}")


def descargar_documento(
    nombre_archivo,
    servidor_host,
    puerto_backend=8080,
    protocolo="http",
    carpeta_destino=None,
):
    """Descarga un documento desde el backend y lo guarda en la carpeta local."""
    ruta_descarga = carpeta_destino or os.path.join(obtener_directorio_base(), "descargas")
    os.makedirs(ruta_descarga, exist_ok=True)

    nombre_archivo_seguro = os.path.basename(nombre_archivo)
    archivo_url = quote(nombre_archivo_seguro)
    url = f"{protocolo}://{servidor_host}:{puerto_backend}/api/download/{archivo_url}"

    try:
        respuesta = requests.get(url, timeout=30)
        if respuesta.status_code == 200:
            ruta_archivo = os.path.join(ruta_descarga, nombre_archivo_seguro)
            with open(ruta_archivo, "wb") as archivo_descargado:
                archivo_descargado.write(respuesta.content)
            logger.info(f"Documento descargado: {ruta_archivo}")
            return ruta_archivo

        logger.error(f"Error al descargar desde {url}: {respuesta.status_code} - {respuesta.text}")
        return None
    except Exception as e:
        logger.error(f"Error en la descarga desde {url}: {e}")
        return None


def abrir_archivo_descargado(ruta_archivo):
    """Abre el archivo descargado con la aplicación predeterminada del sistema."""
    try:
        os.startfile(ruta_archivo)
        logger.info(f"Archivo abierto automáticamente: {ruta_archivo}")
        return True
    except OSError as e:
        logger.error(f"No se pudo abrir automáticamente el archivo {ruta_archivo}: {e}")
        return False


def manejar_signal(signum, frame):
    """Maneja señales para shutdown graceful"""
    global server_running, app_root
    logger.info("Señal de terminación recibida. Cerrando servidor...")
    server_running = False
    if server_socket:
        try:
            server_socket.close()
        except:  # noqa: E722
            pass
    if app_root:
        app_root.after(0, app_root.destroy)
    else:
        sys.exit(0)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ESCLAVO - Servidor de Notificaciones")
    logger.info("=" * 60)
    logger.info(f"HOST: {CONFIG['HOST']}, PORT: {CONFIG['PORT']}")
    logger.info(f"Proceso bloqueante: {CONFIG['PROCESO_BLOQUEANTE']}")

    # Registrar handlers para shutdown graceful
    signal.signal(signal.SIGINT, manejar_signal)
    signal.signal(signal.SIGTERM, manejar_signal)

    try:
        app_root = tk.Tk()
        app_root.withdraw()
        hilo_servidor = threading.Thread(target=iniciar_cliente, daemon=True)
        hilo_servidor.start()
        app_root.after(200, procesar_alertas)
        app_root.mainloop()
    except KeyboardInterrupt:
        logger.info("Interrupción del usuario")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
        sys.exit(1)
