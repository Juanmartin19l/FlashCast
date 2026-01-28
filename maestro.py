import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import font, scrolledtext
import threading
import json
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
PUERTO = 5000
TIMEOUT = 0.3
MAX_HILOS = 500
ARCHIVO_HISTORIAL = "historial_ips.json"


class EnviadorMensajes:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📢 Envío de Mensajes - Panel de Control")
        self.root.geometry("900x700")
        self.root.configure(bg="#2c3e50")

        # Variables para el contador
        self.contador_enviados = 0
        self.lock = threading.Lock()

        # Cargar historial de IPs
        self.historial_ips = self.cargar_historial()

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
        self.boton_enviar.pack(pady=15)

        # Label de estado
        self.label_estado = tk.Label(
            self.root,
            text="Listo para enviar",
            font=font.Font(size=12),
            fg="#ecf0f1",
            bg="#2c3e50",
        )
        self.label_estado.pack(pady=5)

        # Contador de mensajes enviados
        self.label_contador = tk.Label(
            self.root,
            text="📊 Mensajes enviados: 0",
            font=font.Font(size=12, weight="bold"),
            fg="#3498db",
            bg="#2c3e50",
        )
        self.label_contador.pack(pady=5)

        # Frame para el log
        frame_log = tk.Frame(self.root, bg="#2c3e50")
        frame_log.pack(pady=10, padx=30, fill="both", expand=True)

        label_log = tk.Label(
            frame_log,
            text="📋 Log de IPs alcanzadas:",
            font=font.Font(size=12),
            fg="white",
            bg="#2c3e50",
        )
        label_log.pack(anchor="w")

        # Área de log con scroll
        self.log_texto = scrolledtext.ScrolledText(
            frame_log,
            font=font.Font(family="Courier", size=10),
            height=10,
            wrap=tk.WORD,
            bg="#1a1a1a",
            fg="#00ff00",
            state="disabled",
        )
        self.log_texto.pack(fill="both", expand=True, pady=5)

        self.root.mainloop()

    def cargar_historial(self):
        """Carga el historial de IPs contactadas desde el archivo"""
        if os.path.exists(ARCHIVO_HISTORIAL):
            try:
                with open(ARCHIVO_HISTORIAL, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def guardar_historial(self):
        """Guarda el historial de IPs contactadas en el archivo"""
        try:
            with open(ARCHIVO_HISTORIAL, "w") as f:
                json.dump(self.historial_ips, f, indent=2)
        except:
            pass

    def agregar_log(self, texto):
        """Agrega una línea al log de forma segura desde cualquier hilo"""
        self.log_texto.config(state="normal")
        self.log_texto.insert(tk.END, texto + "\n")
        self.log_texto.see(tk.END)  # Auto-scroll al final
        self.log_texto.config(state="disabled")

    def actualizar_contador(self):
        """Actualiza el contador en la UI"""
        self.label_contador.config(
            text=f"📊 Mensajes enviados: {self.contador_enviados}"
        )

    def enviar_a_ip(self, ip, mensaje):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                s.connect((str(ip), PUERTO))
                s.sendall(mensaje.encode("utf-8"))

                # Registrar envío exitoso
                ip_str = str(ip)
                es_repetida = ip_str in self.historial_ips

                with self.lock:
                    self.contador_enviados += 1

                    # Actualizar historial con timestamp
                    self.historial_ips[ip_str] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    # Marcar si es repetida o nueva
                    if es_repetida:
                        self.root.after(
                            0,
                            lambda: self.agregar_log(
                                f"🔄 {ip_str} (ya contactada antes)"
                            ),
                        )
                    else:
                        self.root.after(
                            0, lambda: self.agregar_log(f"✅ {ip_str} (nueva)")
                        )

                    self.root.after(0, self.actualizar_contador)

                return True
        except:
            pass
        return False

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
        # Resetear contador
        with self.lock:
            self.contador_enviados = 0

        # Limpiar log anterior
        self.log_texto.config(state="normal")
        self.log_texto.delete("1.0", tk.END)
        self.log_texto.config(state="disabled")
        self.actualizar_contador()

        self.label_estado.config(
            text="🚀 Enviando mensajes a toda la red...", fg="#f39c12"
        )
        self.agregar_log("🚀 Iniciando envío masivo...")
        self.agregar_log("-" * 50)

        # Primero enviar a IPs conocidas (del historial)
        ips_conocidas = [ipaddress.ip_address(ip) for ip in self.historial_ips.keys()]

        if ips_conocidas:
            self.agregar_log(
                f"⚡ Enviando primero a {len(ips_conocidas)} IPs conocidas..."
            )
            with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
                executor.map(lambda ip: self.enviar_a_ip(ip, mensaje), ips_conocidas)
            self.agregar_log("✅ IPs conocidas procesadas")
            self.agregar_log("-" * 50)

        # Luego escanear toda la red
        self.agregar_log("🔍 Escaneando resto de la red...")
        hosts = self.obtener_mi_red()

        # Filtrar las IPs que ya fueron enviadas
        ips_conocidas_str = set(self.historial_ips.keys())
        hosts_nuevos = [h for h in hosts if str(h) not in ips_conocidas_str]

        with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
            executor.map(lambda ip: self.enviar_a_ip(ip, mensaje), hosts_nuevos)

        # Guardar historial actualizado
        self.guardar_historial()

        self.root.after(0, lambda: self.agregar_log("-" * 50))
        self.root.after(
            0,
            lambda: self.agregar_log(
                f"🏁 Finalizado. Total: {self.contador_enviados} mensajes enviados"
            ),
        )
        self.root.after(
            0,
            lambda: self.agregar_log(
                f"📚 Historial total: {len(self.historial_ips)} IPs únicas contactadas"
            ),
        )

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
