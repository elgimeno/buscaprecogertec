import socket
import tkinter as tk
from tkinter import messagebox
import threading
import time

IP_GERTEC = "192.168.127.5"
PORTA = 6500

class BuscaPrecoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BUSCA PREÇO BONANÇA LJ27")
        self.root.geometry("600x400")
        self.root.configure(bg="#1a1a1a")

        # Título
        self.label_status = tk.Label(root, text="ESCANEIE O PRODUTO", font=("Arial", 18, "bold"), fg="white", bg="#1a1a1a")
        self.label_status.pack(pady=20)

        # Campo de Entrada
        self.entry = tk.Entry(root, font=("Arial", 24), justify="center", width=20)
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.ao_bipar)
        self.entry.focus_set()

        # ÁREA DE RESULTADO (Sempre visível, mas vazia no início)
        self.label_desc = tk.Label(root, text="", font=("Arial", 16), fg="#aaaaaa", bg="#1a1a1a", wraplength=550)
        self.label_desc.pack(pady=20)
        
        self.label_preco = tk.Label(root, text="", font=("Arial", 45, "bold"), fg="#4ade80", bg="#1a1a1a")
        self.label_preco.pack(pady=10)

    def log_local(self, msg):
        with open("DEBUG_INTERFACE.txt", "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")

    def ao_bipar(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if ean:
            self.label_status.config(text="CONSULTANDO", fg="green")
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
            self.log_local(f"Recebido: {texto}")

            if "|" in texto:
                # Pega o trecho que tem o preço
                for parte in texto.split('#'):
                    if "|" in parte:
                        d, p = parte.split('|')
                        self.exibir_na_tela(d.strip(), p.strip())
                        return
            
            self.exibir_na_tela("PRODUTO NÃO ENCONTRADO", "---")
        except Exception as e:
            self.log_local(f"Erro: {str(e)}")
            self.exibir_na_tela("ERRO DE REDE", "OFFLINE")

    def exibir_na_tela(self, desc, preco):
        # Usa o after para garantir que o Tkinter atualize a interface principal
        self.root.after(0, self._atualizar_labels, desc, preco)

    def _atualizar_labels(self, desc, preco):
        self.label_status.config(text="ESCANEIE O PRODUTO", fg="white")
        self.label_desc.config(text=desc.upper())
        self.label_preco.config(text=preco)
        self.log_local(f"Interface atualizada com {desc}")
        
        # Limpa após 4 segundos
        self.root.after(4000, self._limpar_tela)

    def _limpar_tela(self):
        self.label_desc.config(text="")
        self.label_preco.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = BuscaPrecoApp(root)
    root.mainloop()
