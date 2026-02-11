import socket
import tkinter as tk
import threading
import time
import requests
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime

# --- CONFIGURAÇÕES ---
IP_GERTEC = "192.168.127.5"
PORTA_GERTEC = 6500
URL_LISTA_TXT = "https://drive.usercontent.google.com/download?id=1C-c-bGxl_p0rCjOEq_Nw9FK2H2itOyzw&export=download&authuser=0&confirm=t&uuid=7b5e4496-4284-4d90-b63f-93eeaa7f7dc9&at=APcXIO3QW8iIJ3ONowEZrdMqXbZw:1770835577993" # Altere para seu link real

class TerminalLJ27:
    def __init__(self, root):
        self.root = root
        self.root.title("TERMINAL LJ 27")
        self.root.attributes("-fullscreen", True) # Inicia em tela cheia
        self.root.configure(bg="black")
        
        self.is_showing_price = False
        self.last_interaction = time.time()
        self.lista_fotos = []
        self.indice_atual = 0
        self.data_hoje = datetime.now().strftime("%Y-%m-%d")

        # Atalhos de Teclado (F12 e ESC)
        self.root.bind("<F12>", lambda e: self.root.attributes("-fullscreen", True))
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        # Camada 1: Publicidade (Fundo)
        self.foto_label = tk.Label(root, bg="black")
        self.foto_label.pack(expand=True, fill="both")
        
        # Camada 2: Relógio (Canto)
        self.label_relogio = tk.Label(root, text="", font=("Consolas", 14), 
                                      fg="#475569", bg="black", padx=20, pady=10)
        self.label_relogio.place(relx=1.0, rely=1.0, anchor="se")

        # Camada 3: Container de Preço (Escondido)
        self.price_frame = tk.Frame(root, bg="#0f172a")
        self.label_desc = tk.Label(self.price_frame, text="", font=("Segoe UI", 32, "bold"), 
                                   fg="white", bg="#0f172a", wraplength=900)
        self.label_desc.pack(pady=40, expand=True)
        self.label_preco = tk.Label(self.price_frame, text="", font=("Segoe UI", 85, "bold"), 
                                    fg="#4ade80", bg="#0f172a")
        self.label_preco.pack(pady=20, expand=True)

        # Entrada para o Scanner (Sempre focada)
        self.entry = tk.Entry(root)
        self.entry.pack()
        self.entry.bind("<Return>", self.ao_bipar)
        self.entry.focus_set()

        # Loops de Sistema
        threading.Thread(target=self.sincronizar_txt, daemon=True).start()
        self.atualizar_relogio()
        self.ciclo_slideshow()
        self.verificar_inatividade()

    def ao_bipar(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if ean:
            self.exibir_tela_preco(ean)

    def exibir_tela_preco(self, ean):
        self.is_showing_price = True
        self.last_interaction = time.time()
        self.foto_label.pack_forget()
        self.price_frame.pack(expand=True, fill="both")
        self.label_relogio.lift()
        
        self.label_desc.config(text="BUSCANDO...", fg="yellow")
        self.label_preco.config(text="")
        
        # Thread para não travar a tela enquanto espera a rede
        threading.Thread(target=self.consultar_gertec, args=(ean,), daemon=True).start()

    def consultar_gertec(self, ean):
        """Lógica Real de Comunicação TCP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(4)
                s.connect((IP_GERTEC, PORTA_GERTEC))
                
                # Protocolo Gertec: Handshake ID + EAN
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
                
                texto = resp.decode('cp1252', errors='replace')
                
                if "|" in texto:
                    for parte in texto.split('#'):
                        if "|" in parte:
                            desc, preco = parte.split('|')
                            self.root.after(0, self.atualizar_labels_preco, desc.strip(), preco.strip(), True)
                            return
                
                self.root.after(0, self.atualizar_labels_preco, "PRODUTO NÃO ENCONTRADO", "---", False)
        except Exception as e:
            self.root.after(0, self.atualizar_labels_preco, "ERRO DE CONEXÃO", "OFFLINE", False)

    def atualizar_labels_preco(self, desc, preco, sucesso):
        cor_p = "#4ade80" if sucesso else "#f87171"
        self.label_desc.config(text=desc.upper(), fg="white")
        self.label_preco.config(text=preco, fg=cor_p)

    def sincronizar_txt(self):
        """Busca fotos e aplica a regra da meia-noite"""
        while True:
            hoje = datetime.now().strftime("%Y-%m-%d")
            if self.data_hoje != hoje:
                self.lista_fotos = []
                self.data_hoje = hoje

            try:
                r = requests.get(URL_LISTA_TXT, timeout=10)
                if r.status_code == 200:
                    urls = r.text.splitlines()
                    temp_fotos = []
                    for url in urls:
                        if url.strip():
                            # Download da imagem
                            img_res = requests.get(url.strip(), timeout=10).content
                            img = Image.open(BytesIO(img_res))
                            # Redimensionar para o tamanho da tela
                            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                            img = img.resize((w, h), Image.Resampling.LANCZOS)
                            temp_fotos.append(ImageTk.PhotoImage(img))
                    
                    if temp_fotos:
                        self.lista_fotos = temp_fotos
            except:
                pass
            time.sleep(300) # Checa a cada 5 min

    def ciclo_slideshow(self):
        if not self.is_showing_price:
            if self.lista_fotos:
                self.foto_label.configure(image=self.lista_fotos[self.indice_atual], text="")
                self.indice_atual = (self.indice_atual + 1) % len(self.lista_fotos)
            else:
                self.foto_label.configure(image="", text="APROXIME O PRODUTO DO LEITOR\nCONSULTE O PREÇO", 
                                          font=("Segoe UI", 40, "bold"), fg="#1e293b")
        self.root.after(10000, self.ciclo_slideshow)

    def atualizar_relogio(self):
        agora = datetime.now().strftime("%H:%M:%S")
        self.label_relogio.config(text=agora)
        self.root.after(1000, self.atualizar_relogio)

    def verificar_inatividade(self):
        if self.is_showing_price and (time.time() - self.last_interaction > 15):
            self.is_showing_price = False
            self.price_frame.pack_forget()
            self.foto_label.pack(expand=True, fill="both")
            self.entry.focus_set()
        self.root.after(1000, self.verificar_inatividade)

if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalLJ27(root)
    root.mainloop()
