import socket
import tkinter as tk
from tkinter import font
import re


def mostrar_alerta(mensaje):
    root = tk.Tk()
    root.overrideredirect(True)

    # Colores corporativos
    COLOR_AZUL = "#4A90E2"
    COLOR_AZUL_CLARO = "#E8F4FD"
    COLOR_GRIS = "#666666"
    COLOR_BLANCO = "#FFFFFF"
    COLOR_ERROR = "#E74C3C"

    root.attributes("-topmost", True)
    root.configure(bg=COLOR_BLANCO)

    # Centrar ventana
    ancho_ventana = 750
    alto_ventana = 650
    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()
    x = (ancho_pantalla - ancho_ventana) // 2
    y = (alto_pantalla - alto_ventana) // 2

    root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
    root.resizable(False, False)

    # Frame principal con padding
    main_frame = tk.Frame(root, bg=COLOR_BLANCO)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

    # Banner "Notificación Importante"
    banner = tk.Label(
        main_frame,
        text="⚠️ NOTIFICACIÓN IMPORTANTE",
        font=font.Font(family="Segoe UI", size=11, weight="bold"),
        fg=COLOR_AZUL,
        bg=COLOR_AZUL_CLARO,
        anchor="w",
        padx=10,
        pady=10,
    )
    banner.pack(fill=tk.X, pady=(0, 20))

    # Frame externo para el mensaje con sombra
    mensaje_outer_frame = tk.Frame(main_frame, bg="#D0D0D0", relief=tk.FLAT)
    mensaje_outer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    # Frame interno del mensaje con diseño mejorado
    mensaje_frame = tk.Frame(mensaje_outer_frame, bg="#FFFFFF", relief=tk.FLAT)
    mensaje_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    # Canvas con scrollbar para mensajes largos
    canvas = tk.Canvas(mensaje_frame, bg="#FFFFFF", highlightthickness=0)
    scrollbar = tk.Scrollbar(mensaje_frame, orient="vertical", command=canvas.yview)

    # Frame para el contenido del mensaje dentro del canvas
    contenido_frame = tk.Frame(canvas, bg="#FFFFFF", relief=tk.FLAT)

    # Configurar canvas ANTES de crear la ventana
    canvas.configure(yscrollcommand=scrollbar.set)

    # Crear Text widget para mostrar markdown con formato
    # SIN height específico - solo con wrap=tk.WORD y width para controlar el flujo
    mensaje_text = tk.Text(
        contenido_frame,
        font=font.Font(family="Segoe UI", size=16),
        fg="#1a1a1a",
        bg="#FFFFFF",
        wrap=tk.WORD,
        relief=tk.FLAT,
        padx=25,
        pady=30,
        cursor="arrow",
        state="disabled",
        width=70,  # Ancho fijo en caracteres para wrap correcto
    )
    mensaje_text.pack(fill=tk.BOTH, expand=True)

    # Configurar tags para formato Markdown
    mensaje_text.tag_config(
        "h1", font=font.Font(family="Segoe UI", size=24, weight="bold"), spacing3=10
    )
    mensaje_text.tag_config(
        "h2", font=font.Font(family="Segoe UI", size=20, weight="bold"), spacing3=8
    )
    mensaje_text.tag_config(
        "h3", font=font.Font(family="Segoe UI", size=18, weight="bold"), spacing3=6
    )
    mensaje_text.tag_config(
        "bold", font=font.Font(family="Segoe UI", size=16, weight="bold")
    )
    mensaje_text.tag_config(
        "italic", font=font.Font(family="Segoe UI", size=16, slant="italic")
    )
    mensaje_text.tag_config(
        "code",
        font=font.Font(family="Courier", size=14),
        background="#f5f5f5",
        foreground="#c7254e",
    )
    mensaje_text.tag_config("bullet", lmargin1=25, lmargin2=40)
    mensaje_text.tag_config("center", justify="center")

    # Función para procesar y mostrar markdown
    def mostrar_markdown(texto):
        mensaje_text.config(state="normal")
        mensaje_text.delete("1.0", tk.END)

        lineas = texto.split("\n")
        for linea in lineas:
            # Encabezados
            if linea.startswith("### "):
                mensaje_text.insert(tk.END, linea[4:] + "\n", "h3")
            elif linea.startswith("## "):
                mensaje_text.insert(tk.END, linea[3:] + "\n", "h2")
            elif linea.startswith("# "):
                mensaje_text.insert(tk.END, linea[2:] + "\n", "h1")
            # Listas con viñetas
            elif linea.strip().startswith("- ") or linea.strip().startswith("* "):
                mensaje_text.insert(tk.END, "• " + linea.strip()[2:] + "\n", "bullet")
            # Línea normal con formato inline
            else:
                procesar_linea_inline(linea + "\n")

        mensaje_text.config(state="disabled")
        # Actualizar el tamaño del frame contenedor
        contenido_frame.update_idletasks()

    def procesar_linea_inline(linea):
        # Procesar **negrita**, *cursiva*, y `código`
        pos = 0
        while pos < len(linea):
            # Buscar **negrita**
            match_bold = re.search(r"\*\*(.*?)\*\*", linea[pos:])
            # Buscar *cursiva*
            match_italic = re.search(r"\*(.*?)\*", linea[pos:])
            # Buscar `código`
            match_code = re.search(r"`(.*?)`", linea[pos:])

            # Determinar cuál viene primero
            matches = []
            if match_bold:
                matches.append((match_bold.start() + pos, "bold", match_bold))
            if match_italic and (
                not match_bold or match_italic.start() < match_bold.start()
            ):
                matches.append((match_italic.start() + pos, "italic", match_italic))
            if match_code:
                matches.append((match_code.start() + pos, "code", match_code))

            if not matches:
                # No hay más formato, insertar el resto
                mensaje_text.insert(tk.END, linea[pos:])
                break

            # Obtener el match más cercano
            matches.sort()
            start_pos, tipo, match = matches[0]

            # Insertar texto antes del match
            if start_pos > pos:
                mensaje_text.insert(tk.END, linea[pos:start_pos])

            # Insertar texto formateado
            if tipo == "bold":
                mensaje_text.insert(tk.END, match.group(1), "bold")
                pos = start_pos + match.end()
            elif tipo == "italic":
                mensaje_text.insert(tk.END, match.group(1), "italic")
                pos = start_pos + match.end()
            elif tipo == "code":
                mensaje_text.insert(tk.END, match.group(1), "code")
                pos = start_pos + match.end()

    # Mostrar el mensaje con formato Markdown
    mostrar_markdown(mensaje)

    # PASO 1: Actualizar el frame ANTES de crear la ventana en el canvas
    contenido_frame.update_idletasks()

    # PASO 2: Obtener el tamaño real del contenido
    contenido_width = contenido_frame.winfo_reqwidth()
    contenido_height = contenido_frame.winfo_reqheight()

    # PASO 3: Crear ventana en el canvas con el ancho del contenido real
    canvas_window = canvas.create_window(
        (0, 0), window=contenido_frame, anchor="nw", width=contenido_width
    )

    # PASO 4: Configurar scrollregion INMEDIATAMENTE con las coordenadas exactas
    # Esto previene el scroll infinito porque define los límites reales del contenido
    canvas.configure(scrollregion=(0, 0, contenido_width, contenido_height))

    # PASO 5: Vincular reconfiguración solo cuando el canvas se redimensiona
    # Esto mantiene el comportamiento correcto sin ciclos infinitos
    def actualizar_canvas_window(event=None):
        """Actualizar ancho cuando el canvas se redimensiona"""
        if event:
            canvas.itemconfig(canvas_window, width=event.width - 2)

    canvas.bind("<Configure>", actualizar_canvas_window)

    # Vincular la rueda del mouse al canvas para scroll
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Bind para Windows
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    mensaje_text.bind_all("<MouseWheel>", on_mousewheel)

    # Empaquetar canvas y scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Separador
    separator = tk.Frame(main_frame, height=1, bg="#E0E0E0")
    separator.pack(fill=tk.X, pady=20)

    # Instrucciones
    instruccion_frame = tk.Frame(main_frame, bg=COLOR_BLANCO)
    instruccion_frame.pack(fill=tk.X, pady=(0, 10))

    tk.Label(
        instruccion_frame,
        text="Escriba ",
        font=font.Font(family="Segoe UI", size=11),
        fg=COLOR_GRIS,
        bg=COLOR_BLANCO,
    ).pack(side=tk.LEFT)

    tk.Label(
        instruccion_frame,
        text='"CONFIRMAR"',
        font=font.Font(family="Segoe UI", size=11, weight="bold"),
        fg=COLOR_AZUL,
        bg=COLOR_BLANCO,
    ).pack(side=tk.LEFT)

    tk.Label(
        instruccion_frame,
        text=" para confirmar",
        font=font.Font(family="Segoe UI", size=11),
        fg=COLOR_GRIS,
        bg=COLOR_BLANCO,
    ).pack(side=tk.LEFT)

    # Frame para campo de texto y botón (en la misma línea)
    input_frame = tk.Frame(main_frame, bg=COLOR_BLANCO)
    input_frame.pack(fill=tk.X, pady=(0, 5))

    # Campo de texto con borde
    entry_frame = tk.Frame(input_frame, bg="#CCCCCC", bd=1)
    entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

    entry = tk.Entry(
        entry_frame,
        font=font.Font(family="Segoe UI", size=12),
        relief=tk.FLAT,
        bg=COLOR_BLANCO,
        fg="#333333",
    )
    entry.pack(fill=tk.X, padx=1, pady=1, ipady=8)

    # Función para convertir a mayúsculas mientras se escribe
    def a_mayusculas(*args):
        texto = entry_var.get().upper()
        entry_var.set(texto)

    entry_var = tk.StringVar()
    entry_var.trace("w", a_mayusculas)
    entry.config(textvariable=entry_var)

    def verificar_confirmacion(event=None):
        texto = entry.get().strip().upper()
        if texto == "CONFIRMAR":
            root.destroy()
        else:
            error_label.config(
                text='⚠ La palabra debe coincidir con "CONFIRMAR" exactamente'
            )
            entry.delete(0, tk.END)
            # Limpiar el mensaje de error después de 5 segundos
            root.after(5000, lambda: error_label.config(text=""))

    # Botón confirmar al lado del textbox
    boton = tk.Button(
        input_frame,
        text="Confirmar y Cerrar",
        command=verificar_confirmacion,
        font=font.Font(family="Segoe UI", size=12, weight="bold"),
        bg="#7DC4F5",
        fg=COLOR_BLANCO,
        relief=tk.FLAT,
        padx=20,
        pady=8,
        cursor="hand2",
        activebackground="#6AB3E4",
    )
    boton.pack(side=tk.RIGHT, fill=tk.Y)

    # Mensaje de error
    error_label = tk.Label(
        main_frame,
        text="",
        font=font.Font(family="Segoe UI", size=10),
        fg=COLOR_ERROR,
        bg=COLOR_BLANCO,
        anchor="w",
    )
    error_label.pack(fill=tk.X, pady=(0, 5))

    # Nota de contacto
    nota_contacto = tk.Label(
        main_frame,
        text="Cualquier consulta comunicarse con el departamento de coordinación",
        font=font.Font(family="Segoe UI", size=10, slant="italic"),
        fg="#888888",
        bg=COLOR_BLANCO,
    )
    nota_contacto.pack(pady=(0, 0))

    # Permitir Enter para confirmar
    entry.bind("<Return>", verificar_confirmacion)

    # Deshabilitar cierre no autorizado
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    # Focus en el campo de texto
    root.update()
    entry.focus_force()

    root.mainloop()


def iniciar_cliente():
    # Escucha en todas las interfaces en el puerto 5000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5000))
    server.listen(1)

    while True:
        conn, addr = server.accept()
        mensaje = conn.recv(2048).decode("utf-8")
        if mensaje:
            mostrar_alerta(mensaje)
        conn.close()


if __name__ == "__main__":
    iniciar_cliente()
