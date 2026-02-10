import socket
import tkinter as tk
from tkinter import font
import threading
import time

IP_GERTEC = "192.168.127.5"
PORTA = 6500

class BuscaPrecoDinamico:
    def __init__(self, root):
        self.root = root
        self.root.title("TERMINAL DE CONSULTA - BONANÇA 27")
        self.root.geometry("800x600")
        self.root.configure(bg="#0f172a")
        
        self.is_fullscreen = False

        # Atalhos de Teclado
        self.root.bind("<F12>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        # Configuração de Redimensionamento Dinâmico (Grid)
        self.root.grid_rowconfigure(1, weight=1) # O container central cresce
        self.root.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        self.header = tk.Frame(root, bg="#1e293b", height=60)
        self.header.grid(row=0, column=0, sticky="ew")
        
        self.label_titulo = tk.Label(self.header, text="TERMINAL DE CONSULTA - BONANÇA 27", 
                                     font=("Segoe UI", 12, "bold"), fg="#94a3b8", bg="#1e293b")
        self.label_titulo.pack(pady=10)

        # Container Principal
        self.main_container = tk.Frame(root, bg="#0f172a")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Instrução
        self.label_status = tk.Label(self.main_container, text="APROXIME O PRODUTO DO LEITOR", 
                                      fg="#38bdf8", bg="#0f172a")
        self.label_status.grid(row=0, column=0, pady=10)

        # Campo de Entrada (EAN)
        self.entry = tk.Entry(self.main_container, justify="center", bg="#1e293b", 
                              fg="white", insertbackground="white", bd=0)
        self.entry.grid(row=1, column=0, pady=10, ipady=10, sticky="ew", padx=100)
        self.entry.bind("<Return>", self.ao_bipar)
        self.entry.focus_set()

        # Área do Produto
        self.label_desc = tk.Label(self.main_container, text="", fg="white", 
                                   bg="#0f172a", wraplength=1000)
        self.label_desc.grid(row=2, column=0, pady=(40, 0))
        
        self.label_preco = tk.Label(self.main_container, text="", fg="#4ade80", bg="#0f172a")
        self.label_preco.grid(row=3, column=0)

        # Evento para ajustar fontes quando a janela mudar de tamanho
        self.root.bind("<Configure>", self.ajustar_fontes)

    def ajustar_fontes(self, event=None):
        # Lógica simples para escalar fontes baseada na altura da janela
        h = self.root.winfo_height()
        
        # Cálculo de tamanhos dinâmicos
        size_status = max(14, int(h / 30))
        size_desc = max(18, int(h / 20))
        size_preco = max(40, int(h / 8))
        size_ean = max(16, int(h / 35))

        self.label_status.config(font=("Segoe UI", size_status, "bold"))
        self.label_desc.config(font=("Segoe UI", size_desc, "bold"), wraplength=self.root.winfo_width()-100)
        self.label_preco.config(font=("Segoe UI", size_preco, "bold"))
        self.entry.config(font=("Consolas", size_ean))

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = True
        self.root.attributes("-fullscreen", True)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)

    def ao_bipar(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if ean:
            self.label_status.config(text="CONSULTANDO", fg="#fbbf24")
            threading.Thread(target=self.processar_rede, args=(ean,), daemon=True).start()

    def processar_rede(self, ean):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((IP_GERTEC, PORTA))
            s.sendall("#ID|01#".encode('cp1252'))
            time.sleep(0.5)
            s.sendall(f"#{ean}#".encode('cp1252'))
            
            resp = b""
            start = time.time()
            while time.time() - start < 3:
                chunk = s.recv(1024)
                if not chunk: break
                resp += chunk
                if b"|" in resp: break
            s.close()

            texto = resp.decode('cp1252', errors='replace')

            if "|" in texto:
                for parte in texto.split('#'):
                    if "|" in parte:
                        d, p = parte.split('|')
                        self.atualizar_ui(d.strip(), p.strip(), True)
                        return
            
            self.atualizar_ui("PRODUTO NÃO ENCONTRADO", "---", False)
        except:
            self.atualizar_ui("ERRO DE CONEXÃO", "OFFLINE", False)

    def atualizar_ui(self, desc, preco, sucesso):
        self.root.after(0, self._renderizar, desc, preco, sucesso)

    def _renderizar(self, desc, preco, sucesso):
        cor_p = "#4ade80" if sucesso else "#f87171"
        self.label_status.config(text="LEITURA REALIZADA", fg="#94a3b8")
        self.label_desc.config(text=desc.upper())
        self.label_preco.config(text=preco, fg=cor_p)
        self.root.after(5000, self._reset)

    def _reset(self):
        self.label_status.config(text="APROXIME O PRODUTO DO LEITOR", fg="#38bdf8")
        self.label_desc.config(text="")
        self.label_preco.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = BuscaPrecoDinamico(root)
    root.mainloop()
