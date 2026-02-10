import socket
import customtkinter as ctk
import threading
import time

IP_GERTEC = "192.168.127.5"
PORTA = 6500

class BuscaPreco(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Consulta Gertec - LJ 27")
        self.geometry("500x500")
        
        self.label = ctk.CTkLabel(self, text="BIPE O PRODUTO", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)
        
        self.entry = ctk.CTkEntry(self, width=300, font=("Arial", 24), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.iniciar_busca)
        self.entry.focus_set()

        self.modal = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=15)
        self.txt_prod = ctk.CTkLabel(self.modal, text="", font=("Arial", 16, "bold"), wraplength=350)
        self.txt_prod.pack(pady=20)
        self.txt_price = ctk.CTkLabel(self.modal, text="", font=("Arial", 40, "bold"), text_color="#3b82f6")
        self.txt_price.pack(pady=10)

    def iniciar_busca(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, 'end')
        if ean:
            self.label.configure(text="CONSULTANDO...", text_color="yellow")
            threading.Thread(target=self.conectar_e_buscar, args=(ean,), daemon=True).start()

    def conectar_e_buscar(self, ean):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5) # Aumentado para 5s
                s.connect((IP_GERTEC, PORTA))
                
                s.sendall(b"#ID|01#")
                time.sleep(0.6)
                s.sendall(f"#{ean}#".encode('latin-1'))
                
                # Leitura contínua para ignorar os #live?
                dados_acumulados = ""
                start_time = time.time()
                while time.time() - start_time < 3: # Tenta ler por 3 segundos
                    chunk = s.recv(1024).decode('latin-1', errors='ignore')
                    dados_acumulados += chunk
                    if "|" in dados_acumulados:
                        break
                
                # FILTRO DE RESULTADO
                if "|" in dados_acumulados:
                    # Pega a última parte que contém o pipe
                    partes = [p for p in dados_acumulados.split('#') if "|" in p]
                    if partes:
                        item = partes[-1].split('|')
                        self.atualizar_tela(item[0], item[1])
                        return

                self.atualizar_tela("NÃO LOCALIZADO", "---", "red")
        except Exception as e:
            self.atualizar_tela("ERRO DE REDE", "OFFLINE", "red")

    def atualizar_tela(self, desc, preco, cor="white"):
        self.after(0, self._exibir, desc, preco, cor)

    def _exibir(self, desc, preco, cor):
        self.label.configure(text="BIPE O PRODUTO", text_color="white")
        self.txt_prod.configure(text=desc.upper(), text_color="white")
        self.txt_price.configure(text=preco)
        self.modal.place(relx=0.5, rely=0.6, anchor="center", width=400, height=250)
        # Se for erro, fica mais tempo na tela (4s), se for preço, 2.5s
        tempo = 4000 if preco == "---" or preco == "OFFLINE" else 2500
        self.after(tempo, lambda: self.modal.place_forget())

if __name__ == "__main__":
    app = BuscaPreco()
    app.mainloop()
