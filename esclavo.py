import socket
import tkinter as tk
from tkinter import font
import winsound
import threading


def sonar_alarma():
    # Sonido de alarma continuo
    for _ in range(5):  # 5 beeps
        winsound.Beep(1000, 300)  # 1000Hz por 300ms


def mostrar_alerta(mensaje):
    root = tk.Tk()

    # Eliminar barra de título y botones PRIMERO
    root.overrideredirect(True)

    root.attributes("-topmost", True)  # Lo pone por encima de TODO
    root.configure(bg="red")  # Fondo rojo para urgencia

    # Forzar actualización para obtener dimensiones correctas
    root.update_idletasks()

    # Obtener dimensiones de la pantalla
    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()

    # Ajustar tamaño para dejar visible la barra de tareas (restar ~60px)
    altura_ventana = alto_pantalla - 60

    # Configurar geometría y forzar posición
    root.geometry(f"{ancho_pantalla}x{altura_ventana}+0+0")
    root.state("normal")
    root.resizable(False, False)

    # Reproducir sonido de alarma en otro hilo
    threading.Thread(target=sonar_alarma, daemon=True).start()

    # Fuente grande y en negrita
    fuente = font.Font(family="Arial", size=48, weight="bold")

    # Título parpadeante
    titulo = tk.Label(
        root, text="⚠️ MENSAJE URGENTE ⚠️", font=fuente, fg="yellow", bg="red"
    )
    titulo.pack(pady=50)

    # Hacer que el título parpadee
    def parpadear():
        color_actual = titulo.cget("fg")
        nuevo_color = "yellow" if color_actual == "white" else "white"
        titulo.config(fg=nuevo_color)
        root.after(500, parpadear)

    parpadear()

    # Mensaje principal
    fuente_mensaje = font.Font(family="Arial", size=32)
    label = tk.Label(
        root,
        text=mensaje,
        font=fuente_mensaje,
        fg="white",
        bg="red",
        wraplength=root.winfo_screenwidth() - 100,
    )
    label.pack(expand=True, pady=20)

    # Instrucciones
    instruccion = tk.Label(
        root,
        text='Escribe "confirmar" para cerrar:',
        font=font.Font(size=24),
        fg="white",
        bg="red",
    )
    instruccion.pack(pady=10)

    # Campo de texto
    entry = tk.Entry(root, font=font.Font(size=24), width=20, justify="center")
    entry.pack(pady=10)

    # Mensaje de error
    error_label = tk.Label(
        root, text="", font=font.Font(size=18), fg="yellow", bg="red"
    )
    error_label.pack(pady=5)

    def verificar_confirmacion(event=None):
        texto = entry.get().strip().lower()
        if texto == "confirmar":
            root.destroy()
        else:
            error_label.config(text="❌ Debes escribir exactamente: confirmar")
            entry.delete(0, tk.END)
            winsound.Beep(500, 200)  # Sonido de error

    # Botón para confirmar
    boton = tk.Button(
        root,
        text="ACEPTAR",
        command=verificar_confirmacion,
        font=font.Font(size=24, weight="bold"),
        bg="yellow",
        fg="red",
        padx=40,
        pady=20,
    )
    boton.pack(pady=20)

    # Nota de contacto
    nota_contacto = tk.Label(
        root,
        text="Cualquier consulta comunicarse con el departamento de coordinación",
        font=font.Font(size=16, slant="italic"),
        fg="white",
        bg="red",
    )
    nota_contacto.pack(pady=15)

    # También permitir Enter para confirmar
    entry.bind("<Return>", verificar_confirmacion)

    # Deshabilitar todas las formas de cerrar
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    for key in ["<Escape>", "<Alt-F4>", "<Control-w>", "<Control-q>"]:
        root.bind(key, lambda e: None)

    # Forzar focus en el campo de texto después de que se renderice la ventana
    root.update()
    entry.focus_force()
    entry.icursor(tk.END)

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
