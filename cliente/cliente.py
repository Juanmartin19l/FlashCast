import socket
import tkinter as tk
from tkinter import font
import logging
import threading
import signal
import sys
import os
import subprocess
from datetime import datetime


# Configuración de logging
def configurar_logging():
    """Configura el sistema de logging para producción"""
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
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


logger = configurar_logging()

# Configuración global (hardcodeada)
CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "TIMEOUT": 30,
    "MAX_BUFFER": 8192,
    "CONFIRMATION_WORD": "CONFIRMAR",
    "PROCESO_BLOQUEANTE": "MacroRecorder.exe",
}

server_running = True
server_socket = None


def proceso_esta_abierto(nombre_proceso):
    """Verifica si un proceso está abierto usando tasklist"""
    try:
        resultado = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {nombre_proceso}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Si el proceso está en la lista, tasklist lo retorna
        return nombre_proceso.lower() in resultado.stdout.lower()
    except Exception as e:
        logger.error(f"Error verificando proceso {nombre_proceso}: {e}")
        return False


def mostrar_alerta(mensaje):
    root = tk.Tk()
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
    alto_ventana = 600
    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()
    x = (ancho_pantalla - ancho_ventana) // 2
    y = (alto_pantalla - alto_ventana) // 2

    root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
    root.resizable(False, False)

    # Frame principal con padding
    main_frame = tk.Frame(root, bg=COLOR_FONDO)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=24)

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

    # Frame externo para el mensaje con borde sutil
    mensaje_outer_frame = tk.Frame(main_frame, bg=COLOR_BORDE)
    mensaje_outer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

    # Frame interno del mensaje con diseño limpio
    mensaje_frame = tk.Frame(mensaje_outer_frame, bg=COLOR_BLANCO)
    mensaje_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    # Canvas con scrollbar para mensajes largos
    canvas = tk.Canvas(mensaje_frame, bg=COLOR_BLANCO, highlightthickness=0)
    scrollbar = tk.Scrollbar(mensaje_frame, orient="vertical", command=canvas.yview)

    # Frame para el contenido del mensaje dentro del canvas
    contenido_frame = tk.Frame(canvas, bg=COLOR_BLANCO)

    # Configurar canvas ANTES de crear la ventana
    canvas.configure(yscrollcommand=scrollbar.set)

    mensaje_text = tk.Text(
        contenido_frame,
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
    )
    mensaje_text.pack(fill=tk.BOTH, expand=True)

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
        # Actualizar el tamaño del frame contenedor
        contenido_frame.update_idletasks()

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

    contenido_frame.update_idletasks()
    contenido_width = contenido_frame.winfo_reqwidth()
    contenido_height = contenido_frame.winfo_reqheight()

    canvas_window = canvas.create_window(
        (0, 0), window=contenido_frame, anchor="nw", width=contenido_width
    )

    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    def actualizar_canvas_window(event=None):
        """Actualizar ancho cuando el canvas se redimensiona"""
        if event:
            canvas.itemconfig(canvas_window, width=event.width - 2)

    canvas.bind("<Configure>", actualizar_canvas_window)

    def on_mousewheel(event):
        if contenido_height > canvas.winfo_height():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.focus_set()
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    # Empaquetar canvas y scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Separador
    separator = tk.Frame(main_frame, height=1, bg=COLOR_BORDE)
    separator.pack(fill=tk.X, pady=4)

    # Instrucciones
    instruccion_frame = tk.Frame(main_frame, bg=COLOR_FONDO)
    instruccion_frame.pack(fill=tk.X, pady=(8, 12))

    tk.Label(
        instruccion_frame,
        text="Escriba ",
        font=font.Font(family="Segoe UI", size=10),
        fg=COLOR_TEXTO_SECUNDARIO,
        bg=COLOR_FONDO,
    ).pack(side=tk.LEFT)

    tk.Label(
        instruccion_frame,
        text='"CONFIRMAR"',
        font=font.Font(family="Segoe UI", size=10, weight="bold"),
        fg=COLOR_PRIMARIO,
        bg=COLOR_FONDO,
    ).pack(side=tk.LEFT)

    tk.Label(
        instruccion_frame,
        text=" para cerrar.",
        font=font.Font(family="Segoe UI", size=10),
        fg=COLOR_TEXTO_SECUNDARIO,
        bg=COLOR_FONDO,
    ).pack(side=tk.LEFT)

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

    def verificar_confirmacion(event=None):
        texto = entry.get().strip().upper()
        if texto == CONFIG["CONFIRMATION_WORD"]:
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

    root.mainloop()


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

                    # Verificar si el proceso bloqueante está abierto
                    if proceso_esta_abierto(CONFIG["PROCESO_BLOQUEANTE"]):
                        logger.warning(
                            f"Proceso {CONFIG['PROCESO_BLOQUEANTE']} está activo. Mensaje DESCARTADO."
                        )
                        # No se encola ni se muestra el mensaje
                    else:
                        # Ejecutar en thread separado para no bloquear el servidor
                        thread = threading.Thread(
                            target=mostrar_alerta, args=(mensaje,)
                        )
                        thread.daemon = True
                        thread.start()

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


def manejar_signal(signum, frame):
    """Maneja señales para shutdown graceful"""
    global server_running
    logger.info("Señal de terminación recibida. Cerrando servidor...")
    server_running = False
    if server_socket:
        try:
            server_socket.close()
        except:  # noqa: E722
            pass
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
        iniciar_cliente()
    except KeyboardInterrupt:
        logger.info("Interrupción del usuario")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
        sys.exit(1)
