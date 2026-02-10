import socket
import customtkinter as ctk
import threading
import time

# Configurações da LJ 27
IP_GERTEC = "192.168.127.5"
PORTA = 6500

class BuscaPreco(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Consulta Gertec - LJ 27")
        self.geometry("500x500")
        
        # UI Principal
        self.label = ctk.CTkLabel(self, text="ESCANEIE O PRODUTO", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)
        
        self.entry = ctk.CTkEntry(self, width=300, font=("Arial", 24), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.iniciar_busca)
        self.entry.focus_set()

        # Modal de Resultado (Forçado por cima)
        self.modal = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=15)
        self.txt_prod = ctk.CTkLabel(self.modal, text="", font=("Arial", 16, "bold"), wraplength=350)
        self.txt_prod.pack(pady=20)
        self.txt_price = ctk.CTkLabel(self.modal, text="", font=("Arial", 40, "bold"), text_color="#3b82f6")
        self.txt_price.pack(pady=10)

    def iniciar_busca(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, 'end')
        if ean:
            # Roda a conexão em "segundo plano" para não travar a janela
            threading.Thread(target=self.conectar_e_buscar, args=(ean,), daemon=True).start()

    def conectar_e_buscar(self, ean):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((IP_GERTEC, PORTA))
                
                # Handshake e Consulta
                s.sendall(b"#ID|01#")
                time.sleep(0.5)
                s.sendall(f"#{ean}#".encode('latin-1'))
                
                # Captura bruta da resposta
                raw_data = s.recv(1024)
                # Tenta decodificar ignorando erros de acentuação (comum em lojas)
                res = raw_data.decode('latin-1', errors='ignore')

                if "|" in res:
                    partes = res.split('#')[-1].split('|')
                    self.atualizar_tela(partes[0].strip(), partes[1].strip())
                else:
                    self.atualizar_tela("PRODUTO NÃO ENCONTRADO", "---")
        except Exception as e:
            self.atualizar_tela("ERRO DE CONEXÃO", "OFFLINE")

    def atualizar_tela(self, desc, preco):
        # O CustomTkinter exige que atualizações de tela venham da thread principal
        self.after(0, self._exibir, desc, preco)

    def _exibir(self, desc, preco):
        self.txt_prod.configure(text=desc.upper())
        self.txt_price.configure(text=preco)
        self.modal.place(relx=0.5, rely=0.6, anchor="center", width=400, height=250)
        self.after(2500, lambda: self.modal.place_forget())

if __name__ == "__main__":
    app = BuscaPreco()
    app.mainloop()
