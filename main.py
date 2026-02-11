import socket
import tkinter as tk
import threading
import time
import requests
import os
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime

# Configurações
IP_GERTEC = "192.168.127.5"
PORTA_GERTEC = 6500
URL_LISTA_FOTOS = "http://seu-servidor.com/lista_promos.txt"

class TerminalLJFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("TERMINAL LJ 27")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        
        self.is_showing_price = False
        self.last_interaction = time.time()
        self.lista_imagens = []
        self.indice_atual = 0
        self.data_ultima_atualizacao = ""

        # Camada de Fundo (Fotos)
        self.foto_label = tk.Label(root, bg="black")
        self.foto_label.pack(expand=True, fill="both")
        
        # Relógio no Canto Inferior Direito
        self.label_relogio = tk.Label(root, text="", font=("Consolas", 14), 
                                      fg="#475569", bg="black", padx=20, pady=10)
        self.label_relogio.place(relx=1.0, rely=1.0, anchor="se")

        # UI de Preço (Centralizada)
        self.price_frame = tk.Frame(root, bg="#0f172a")
        self.label_desc = tk.Label(self.price_frame, text="", font=("Segoe UI", 35, "bold"), fg="white", bg="#0f172a", wraplength=900)
        self.label_desc.pack(pady=40)
        self.label_preco = tk.Label(self.price_frame, text="", font=("Segoe UI", 90, "bold"), fg="#4ade80", bg="#0f172a")
        self.label_preco.pack()

        # Input invisível
        self.entry = tk.Entry(root)
        self.entry.pack()
        self.entry.bind("<Return>", self.on_scan)
        self.entry.focus_set()

        # Iniciar Threads e Loops
        threading.Thread(target=self.gerenciar_conteudo_remoto, daemon=True).start()
        self.atualizar_relogio()
        self.ciclo_slideshow()
        self.check_idle()

    def atualizar_relogio(self):
        """Atualiza o horário na tela a cada segundo"""
        agora = datetime.now().strftime("%H:%M:%S")
        self.label_relogio.config(text=agora)
        # Se estiver em modo preço, o relógio pode ficar branco para melhor leitura
        self.label_relogio.config(fg="white" if self.is_showing_price else "#475569")
        self.root.after(1000, self.atualizar_relogio)

    def gerenciar_conteudo_remoto(self):
        while True:
            hoje = datetime.now().strftime("%Y-%m-%d")

            # Reset de Meia-Noite
            if self.data_ultima_atualizacao != hoje:
                self.lista_imagens = []
                print("Segurança: Limpando ofertas vencidas.")

            try:
                r = requests.get(URL_LISTA_FOTOS, timeout=5)
                if r.status_code == 200:
                    urls = r.text.splitlines()
                    if urls:
                        novas_imgs = []
                        for url in urls:
                            if url.strip():
                                img_data = requests.get(url.strip(), timeout=5).content
                                img = Image.open(BytesIO(img_data))
                                w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
                                img = img.resize((w, h), Image.Resampling.LANCZOS)
                                novas_imgs.append(ImageTk.PhotoImage(img))
                        
                        if novas_imgs:
                            self.lista_imagens = novas_imgs
                            self.data_ultima_atualizacao = hoje
            except:
                pass

            time.sleep(300) # Verifica o servidor a cada 5 min

    def ciclo_slideshow(self):
        if not self.is_showing_price:
            if self.lista_imagens:
                self.foto_label.configure(image=self.lista_imagens[self.indice_atual], text="")
                self.indice_atual = (self.indice_atual + 1) % len(self.lista_imagens)
            else:
                self.foto_label.configure(image="", text="CONSULTE O PREÇO AQUI\nLJ 27", 
                                          font=("Segoe UI", 40, "bold"), fg="#1e293b")
        
        self.root.after(10000, self.ciclo_slideshow)

    def on_scan(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if ean:
            self.show_price(ean)

    def show_price(self, ean):
        self.is_showing_price = True
        self.last_interaction = time.time()
        self.foto_label.pack_forget()
        self.price_frame.pack(expand=True, fill="both")
        self.label_relogio.lift() # Mantém o relógio por cima do frame de preço
        
        # Sua lógica de socket Gertec aqui...
        self.label_desc.config(text="CONSULTANDO...")
        # threading.Thread(target=self.query_gertec, args=(ean,)).start()

    def check_idle(self):
        if self.is_showing_price and (time.time() - self.last_interaction > 15):
            self.is_showing_price = False
            self.price_frame.pack_forget()
            self.foto_label.pack(expand=True, fill="both")
        self.root.after(1000, self.check_idle)

if __name__ == "__main__":
    root = tk.Tk()
    app = TerminalLJFinal(root)
    root.mainloop()
