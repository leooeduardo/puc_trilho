"""
Visualizador de Encoders ESP32 - Python
Lê dados JSON da serial e permite zerar o encoder via botão ou tecla 'R'
"""
import tkinter as tk
from tkinter import font as tkfont
import serial
import serial.tools.list_ports
import threading
import json
import time

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
BAUD = 115200
BG        = "#121212"
BG2       = "#1e1e1e"
BG3       = "#2a2a2a"
ACCENT    = "#00d2ff"
ACCENT2   = "#ff007c"
GREEN     = "#00ff88"
ORANGE    = "#ff9800"
RED       = "#ff4500"
YELLOW    = "#ffeb3b"
FG        = "#ffffff"
FG2       = "#aaaaaa"

class ESP32Viewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Encoders ESP32")
        self.root.configure(bg=BG)
        self.root.geometry("560x680")
        self.root.resizable(False, False)

        self.ser = None
        self.running = False
        self.thread = None

        self._build_ui()
        self.root.bind("<Key>", self._on_key)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        title_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        label_font = tkfont.Font(family="Segoe UI", size=9)
        value_font = tkfont.Font(family="Segoe UI", size=36, weight="bold")
        value2_font = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        btn_font   = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        log_font   = tkfont.Font(family="Courier New", size=9)

        # ── Título ──────────────────────────────
        tk.Label(self.root, text="Visualizador de Encoders ESP32",
                 bg=BG, fg=FG, font=title_font).pack(pady=(18, 4))

        # ── Conexão ─────────────────────────────
        conn_frame = tk.Frame(self.root, bg=BG)
        conn_frame.pack(fill="x", padx=24, pady=(0, 8))

        tk.Label(conn_frame, text="Porta:", bg=BG, fg=FG2, font=label_font).pack(side="left")
        self.port_var = tk.StringVar(value="COM3")
        self.port_entry = tk.Entry(conn_frame, textvariable=self.port_var,
                                   width=8, bg=BG3, fg=FG, relief="flat",
                                   font=btn_font, insertbackground=FG)
        self.port_entry.pack(side="left", padx=(4,8))

        self.conn_btn = tk.Button(conn_frame, text="Conectar", bg="#0078d4", fg=FG,
                                  font=btn_font, relief="flat", padx=14,
                                  command=self._toggle_connect, cursor="hand2")
        self.conn_btn.pack(side="left")

        self.status_lbl = tk.Label(conn_frame, text="● Desconectado",
                                   bg=BG, fg="#ff4040", font=label_font)
        self.status_lbl.pack(side="left", padx=10)

        # ── E6B2 ────────────────────────────────
        e6b2_frame = tk.Frame(self.root, bg=BG2, bd=0, relief="flat")
        e6b2_frame.pack(fill="x", padx=24, pady=6)
        e6b2_frame.configure(padx=16, pady=12)

        tk.Label(e6b2_frame, text="Encoder Industrial (E6B2-CWZ3E)",
                 bg=BG2, fg=FG, font=btn_font).pack(anchor="w")
        tk.Label(e6b2_frame, text="Pinos 18 e 19", bg=BG2, fg=FG2, font=label_font).pack(anchor="w")
        self.val_e6b2 = tk.Label(e6b2_frame, text="0", bg=BG2, fg=ACCENT, font=value_font)
        self.val_e6b2.pack()

        sep = tk.Frame(e6b2_frame, bg="#444444", height=1)
        sep.pack(fill="x", pady=(8,8))

        tk.Label(e6b2_frame, text="Fim de Curso — Pino 27", bg=BG2, fg=FG2, font=label_font).pack(anchor="w")
        self.val_lim = tk.Label(e6b2_frame, text="Esperando fim de curso...",
                                bg=BG2, fg=RED, font=value2_font)
        self.val_lim.pack(pady=(2,6))

        tk.Label(e6b2_frame, text='Tecla "R" para ZERAR manualmente',
                 bg=BG2, fg=YELLOW, font=label_font).pack()

        self.reset_btn = tk.Button(e6b2_frame, text="Zerar Agora  (R)",
                                   bg=ORANGE, fg="#1e1e1e", font=btn_font,
                                   relief="flat", padx=16, pady=6,
                                   command=self._send_reset, cursor="hand2")
        self.reset_btn.pack(pady=(8,0))

        # ── KY-040 ──────────────────────────────
        ky_frame = tk.Frame(self.root, bg=BG2)
        ky_frame.pack(fill="x", padx=24, pady=6)
        ky_frame.configure(padx=16, pady=12)

        tk.Label(ky_frame, text="Rotary Encoder (KY-040)",
                 bg=BG2, fg=FG, font=btn_font).pack(anchor="w")
        tk.Label(ky_frame, text="Pinos 25, 33 (Giro) e 32 (Click)",
                 bg=BG2, fg=FG2, font=label_font).pack(anchor="w")
        self.val_ky040 = tk.Label(ky_frame, text="0", bg=BG2, fg=ACCENT2, font=value_font)
        self.val_ky040.pack()
        self.val_btn = tk.Label(ky_frame, text="Botão Liberado",
                                bg=BG2, fg="#888888", font=value2_font)
        self.val_btn.pack()

        # ── Logs ────────────────────────────────
        tk.Label(self.root, text="Logs:", bg=BG, fg=FG2, font=label_font,
                 anchor="w").pack(fill="x", padx=24)
        log_frame = tk.Frame(self.root, bg="black")
        log_frame.pack(fill="x", padx=24, pady=(2,16))

        self.log_text = tk.Text(log_frame, height=7, bg="black", fg=GREEN,
                                font=log_font, relief="flat",
                                state="disabled", wrap="word")
        self.log_text.pack(fill="x")

    def _log(self, msg):
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", "> " + msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(0, _do)

    def _toggle_connect(self):
        if self.ser and self.ser.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_var.get().strip()
        try:
            self.ser = serial.Serial(port, BAUD, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            self.conn_btn.configure(text="Desconectar", bg="#c0392b")
            self.status_lbl.configure(text="● Conectado", fg=GREEN)
            self._log(f"Conectado em {port} @ {BAUD}")
            self._log("Aguardando ESP32 iniciar... (3s)")
        except Exception as e:
            self._log(f"Erro: {e}")

    def _disconnect(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except: pass
            self.ser = None
        self.conn_btn.configure(text="Conectar", bg="#0078d4")
        self.status_lbl.configure(text="● Desconectado", fg="#ff4040")
        self._log("Desconectado.")

    def _read_loop(self):
        # Aguarda a ESP32 bootar após o reset via DTR (CH340)
        boot_wait = 2.5
        for i in range(int(boot_wait * 10)):
            if not self.running:
                return
            time.sleep(0.1)
        # Limpa buffer do boot
        if self.ser and self.ser.is_open:
            self.ser.reset_input_buffer()
        self._log("ESP32 pronta! Lendo dados...")
        
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._update_ui(data)
                except json.JSONDecodeError:
                    if line:
                        self._log(f"[ESP32] {line}")
            except Exception as e:
                if self.running:
                    self._log(f"Erro leitura: {e}")
                break

    def _update_ui(self, data):
        def _do():
            if "e6b2" in data:
                self.val_e6b2.configure(text=str(data["e6b2"]))
            if "ky040" in data:
                self.val_ky040.configure(text=str(data["ky040"]))
            if "msg" in data:
                self._log("[ESP32] " + str(data["msg"]))
            if "dbg" in data:
                self._log(f"[ECHO] byte={data.get('val','?')}")
            if data.get("btn") is True:
                self.val_btn.configure(text="CLICADO!", fg="#1e1e1e", bg=GREEN)
                self.root.after(400, lambda: self.val_btn.configure(
                    text="Botão Liberado", fg="#888888", bg=BG2))
            if data.get("lim_sw") is True:
                self.val_lim.configure(text="ZERO ALCANÇADO!", bg=RED, fg="#1e1e1e")
                self.root.after(500, lambda: self.val_lim.configure(
                    text="Esperando fim de curso...", bg=BG2, fg=RED))
        self.root.after(0, _do)

    def _send_reset(self):
        if not self.ser or not self.ser.is_open:
            self._log("Conecte primeiro!")
            return
        try:
            self.ser.write(b"R\n")
            self.ser.flush()
            self._log("Enviado 'R' — zerando encoder...")
        except Exception as e:
            self._log(f"Erro ao enviar: {e}")

    def _on_key(self, event):
        if event.char.lower() == 'r':
            self._send_reset()

    def _on_close(self):
        self._disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ESP32Viewer(root)
    root.mainloop()
