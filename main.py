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
        
        self.label = ctk.CTkLabel(self, text="BIPE O PRODUTO", font=("Arial", 22, "bold"))
        self.label.pack(pady=30)
        
        self.entry = ctk.CTkEntry(self, width=350, height=50, font=("Arial", 26), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.iniciar_busca)
        self.entry.focus_set()

        self.modal = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=20)
        self.txt_prod = ctk.CTkLabel(self.modal, text="", font=("Arial", 18, "bold"), wraplength=380, text_color="white")
        self.txt_prod.pack(pady=25)
        self.txt_price = ctk.CTkLabel(self.modal, text="", font=("Arial", 48, "bold"), text_color="#3b82f6")
        self.txt_price.pack(pady=10)

    def iniciar_busca(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, 'end')
        if ean:
            self.label.configure(text="BUSCANDO...", text_color="#fbbf24")
            threading.Thread(target=self.conectar_e_buscar, args=(ean,), daemon=True).start()

    def conectar_e_buscar(self, ean):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((IP_GERTEC, PORTA))

            # Handshake e Consulta (Protocolo validado pelo log)
            s.sendall("#ID|01#".encode('cp1252'))
            time.sleep(0.6)
            s.sendall(f"#{ean}#".encode('cp1252'))

            # Captura de dados
            resposta_bruta = b""
            start = time.time()
            while time.time() - start < 3:
                chunk = s.recv(1024)
                if not chunk: break
                resposta_bruta += chunk
                if b"|" in resposta_bruta: break
            s.close()

            texto = resposta_bruta.decode('cp1252', errors='replace')

            # NOVA LÓGICA DE FILTRO: Procura o PIPE em qualquer lugar da string
            if "|" in texto:
                # Divide a string e procura o pedaço que contém o "|"
                partes = texto.split('#')
                for p in partes:
                    if "|" in p:
                        dados = p.split('|')
                        self.atualizar_tela(dados[0].strip(), dados[1].strip())
                        return

            self.atualizar_tela("NÃO ENCONTRADO", "---", "orange")
            
        except Exception as e:
            self.atualizar_tela("ERRO DE REDE", "OFFLINE", "red")

    def atualizar_tela(self, desc, preco, cor_texto="white"):
        self.after(0, self._exibir, desc, preco, cor_texto)

    def _exibir(self, desc, preco, cor_texto):
        self.label.configure(text="BIPE O PRODUTO", text_color="white")
        self.txt_prod.configure(text=desc.upper())
        self.txt_price.configure(text=preco, text_color="#3b82f6" if preco != "---" else "red")
        self.modal.place(relx=0.5, rely=0.6, anchor="center", width=440, height=280)
        self.after(3000, lambda: self.modal.place_forget())

if __name__ == "__main__":
    app = BuscaPreco()
    app.mainloop()
