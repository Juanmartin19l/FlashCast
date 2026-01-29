import socket
import tkinter as tk
from tkinter import font


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

    # Configurar canvas
    canvas.configure(yscrollcommand=scrollbar.set)

    # Determinar si el mensaje es largo (más de 150 caracteres = negrita, menos = normal)
    es_largo = len(mensaje) > 150
    peso_fuente = "normal" if es_largo else "bold"

    # Mostrar el mensaje dinámico del maestro con formato adaptativo
    mensaje_texto = tk.Label(
        contenido_frame,
        text=mensaje,
        font=font.Font(family="Segoe UI", size=16, weight=peso_fuente),
        fg="#1a1a1a",
        bg="#FFFFFF",
        anchor="center",
        justify=tk.CENTER,
        wraplength=650,
        padx=25,
        pady=30,
    )
    mensaje_texto.pack(fill=tk.BOTH, expand=True)

    # Crear ventana en el canvas
    canvas_window = canvas.create_window(
        (0, 0), window=contenido_frame, anchor="nw", width=690
    )

    # Actualizar scroll region cuando cambie el tamaño
    def configurar_scroll(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=event.width)

    contenido_frame.bind("<Configure>", configurar_scroll)
    canvas.bind(
        "<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)
    )

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

    # Campo de texto con borde
    entry_frame = tk.Frame(main_frame, bg="#CCCCCC", bd=1)
    entry_frame.pack(fill=tk.X, pady=(0, 5))

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

    # Mensaje de error
    error_label = tk.Label(
        main_frame,
        text="",
        font=font.Font(family="Segoe UI", size=10),
        fg=COLOR_ERROR,
        bg=COLOR_BLANCO,
        anchor="w",
    )
    error_label.pack(fill=tk.X, pady=(0, 10))

    def verificar_confirmacion(event=None):
        texto = entry.get().strip().upper()
        if texto == "CONFIRMAR":
            root.destroy()
        else:
            error_label.config(
                text='⚠ La palabra debe coincidir con "CONFIRMAR" exactamente'
            )
            entry.delete(0, tk.END)

    # Frame para botón y nota
    bottom_frame = tk.Frame(main_frame, bg=COLOR_BLANCO)
    bottom_frame.pack(fill=tk.X, pady=(5, 0))

    # Botón confirmar
    boton = tk.Button(
        bottom_frame,
        text="Confirmar y Cerrar",
        command=verificar_confirmacion,
        font=font.Font(family="Segoe UI", size=12, weight="bold"),
        bg="#7DC4F5",
        fg=COLOR_BLANCO,
        relief=tk.FLAT,
        padx=35,
        pady=12,
        cursor="hand2",
        activebackground="#6AB3E4",
    )
    boton.pack(side=tk.RIGHT)

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
        mensaje = conn.recv(1024).decode("utf-8")
        if mensaje:
            mostrar_alerta(mensaje)
        conn.close()


if __name__ == "__main__":
    iniciar_cliente()
