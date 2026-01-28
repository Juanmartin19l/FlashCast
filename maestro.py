import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import font, scrolledtext
import threading

# --- CONFIGURACIÓN ---
PUERTO = 5000
TIMEOUT = 0.3
MAX_HILOS = 500


class EnviadorMensajes:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📢 Envío de Mensajes - Panel de Control")
        self.root.geometry("700x550")
        self.root.configure(bg="#2c3e50")

        # Título
        titulo_font = font.Font(family="Arial", size=24, weight="bold")
        titulo = tk.Label(
            self.root,
            text="📢 Panel de Envío de Mensajes",
            font=titulo_font,
            fg="white",
            bg="#2c3e50",
        )
        titulo.pack(pady=20)

        # Frame para el mensaje
        frame_mensaje = tk.Frame(self.root, bg="#2c3e50")
        frame_mensaje.pack(pady=10, padx=30, fill="both", expand=True)

        label_mensaje = tk.Label(
            frame_mensaje,
            text="Escribe tu mensaje:",
            font=font.Font(size=14),
            fg="white",
            bg="#2c3e50",
        )
        label_mensaje.pack(anchor="w")

        # Campo de texto para el mensaje
        self.texto_mensaje = scrolledtext.ScrolledText(
            frame_mensaje,
            font=font.Font(size=12),
            height=8,
            wrap=tk.WORD,
            bg="white",
            fg="black",
        )
        self.texto_mensaje.pack(fill="both", expand=True, pady=5)
        self.texto_mensaje.insert(
            "1.0", "¡ATENCIÓN! Revisar Microsoft Teams ahora mismo."
        )

        # Botón de enviar
        self.boton_enviar = tk.Button(
            self.root,
            text="📤 ENVIAR MENSAJE A TODA LA RED",
            command=self.enviar_mensaje,
            font=font.Font(size=16, weight="bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=15,
            cursor="hand2",
        )
        self.boton_enviar.pack(pady=20)

        # Label de estado
        self.label_estado = tk.Label(
            self.root,
            text="Listo para enviar",
            font=font.Font(size=12),
            fg="#ecf0f1",
            bg="#2c3e50",
        )
        self.label_estado.pack(pady=10)

        self.root.mainloop()

    def enviar_a_ip(self, ip, mensaje):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                s.connect((str(ip), PUERTO))
                s.sendall(mensaje.encode("utf-8"))
        except:
            pass

    def obtener_mi_red(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            mi_ip = s.getsockname()[0]
            red_obj = ipaddress.ip_network(f"{mi_ip}/16", strict=False)
            return red_obj.hosts()
        finally:
            s.close()

    def iniciar_bombardeo(self, mensaje):
        self.label_estado.config(
            text="🚀 Enviando mensajes a toda la red...", fg="#f39c12"
        )
        hosts = self.obtener_mi_red()

        with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
            executor.map(lambda ip: self.enviar_a_ip(ip, mensaje), hosts)

        self.label_estado.config(
            text="✅ ¡Mensajes enviados correctamente!", fg="#27ae60"
        )
        self.boton_enviar.config(state="normal", bg="#27ae60")

    def enviar_mensaje(self):
        mensaje = self.texto_mensaje.get("1.0", tk.END).strip()

        if not mensaje:
            self.label_estado.config(text="❌ Debes escribir un mensaje", fg="#e74c3c")
            return

        # Deshabilitar botón mientras envía
        self.boton_enviar.config(state="disabled", bg="#95a5a6")

        # Ejecutar en hilo separado para no congelar la UI
        threading.Thread(
            target=self.iniciar_bombardeo, args=(mensaje,), daemon=True
        ).start()


if __name__ == "__main__":
    app = EnviadorMensajes()
