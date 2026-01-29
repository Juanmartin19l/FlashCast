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

    # Configurar tags para formato
    mensaje_text.tag_config(
        "h1", font=font.Font(family="Segoe UI", size=24, weight="bold"), spacing3=10
    )
    mensaje_text.tag_config(
        "h2", font=font.Font(family="Segoe UI", size=20, weight="bold"), spacing3=8
    )
    mensaje_text.tag_config(
        "bold", font=font.Font(family="Segoe UI", size=16, weight="bold")
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

    # PASO 1: Actualizar el frame ANTES de crear la ventana en el canvas
    contenido_frame.update_idletasks()

    # PASO 2: Obtener el tamaño real del contenido DESPUÉS de renderizar
    contenido_width = contenido_frame.winfo_reqwidth()
    contenido_height = contenido_frame.winfo_reqheight()

    # PASO 3: Crear ventana en el canvas con el ancho del contenido real
    canvas_window = canvas.create_window(
        (0, 0), window=contenido_frame, anchor="nw", width=contenido_width
    )

    # PASO 4: Actualizar scrollregion DESPUÉS de crear la ventana
    # Esto es crítico para que el scroll funcione correctamente
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    # PASO 5: Vincular reconfiguración solo cuando el canvas se redimensiona
    # Esto mantiene el comportamiento correcto sin ciclos infinitos
    def actualizar_canvas_window(event=None):
        """Actualizar ancho cuando el canvas se redimensiona"""
        if event:
            canvas.itemconfig(canvas_window, width=event.width - 2)

    canvas.bind("<Configure>", actualizar_canvas_window)

    # Vincular la rueda del mouse CORRECTAMENTE
    def on_mousewheel(event):
        # Scroll solo si hay contenido que scrollear
        if contenido_height > canvas.winfo_height():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Asegurar que el canvas tenga el foco y pueda recibir eventos
    canvas.focus_set()

    # Vincular al canvas para capturar eventos de scroll
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    # Empaquetar canvas y scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Separador
    separator = tk.Frame(main_frame, height=1, bg="#E0E0E0")
    separator.pack(fill=tk.X, pady=10)

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
    input_frame.pack(fill=tk.X, pady=(0, 0))

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
