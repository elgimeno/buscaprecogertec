import socket
import customtkinter as ctk
import threading
import time
import os

IP_GERTEC = "192.168.127.5"
PORTA = 6500

class BuscaPreco(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Consulta Gertec Debug - LJ 27")
        self.geometry("500x500")
        
        self.label = ctk.CTkLabel(self, text="BIPE O PRODUTO", font=("Arial", 22, "bold"))
        self.label.pack(pady=30)
        
        self.entry = ctk.CTkEntry(self, width=350, height=50, font=("Arial", 26), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.iniciar_busca)
        self.entry.focus_set()

        self.modal = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=20)
        self.txt_prod = ctk.CTkLabel(self.modal, text="", font=("Arial", 18, "bold"), wraplength=380)
        self.txt_prod.pack(pady=25)
        self.txt_price = ctk.CTkLabel(self.modal, text="", font=("Arial", 48, "bold"), text_color="#3b82f6")
        self.txt_price.pack(pady=10)

    def log_debug(self, mensagem):
        with open("DEBUG_REDE.txt", "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {mensagem}\n")

    def iniciar_busca(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, 'end')
        if ean:
            self.label.configure(text="BUSCANDO...", text_color="#fbbf24")
            self.log_debug(f"Iniciando busca do EAN: {ean}")
            threading.Thread(target=self.conectar_e_buscar, args=(ean,), daemon=True).start()

    def conectar_e_buscar(self, ean):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(6)
            s.connect((IP_GERTEC, PORTA))
            self.log_debug("Conectado ao servidor.")

            # Handshake
            s.sendall("#ID|01#".encode('cp1252'))
            time.sleep(0.7)
            
            # Envio
            s.sendall(f"#{ean}#".encode('cp1252'))
            self.log_debug("Comandos enviados (#ID e #EAN#).")

            resposta_bruta = b"" # Lendo em BYTES para não dar erro de decode
            start = time.time()
            
            while time.time() - start < 4:
                try:
                    chunk = s.recv(4096)
                    if not chunk: break
                    resposta_bruta += chunk
                    if b"|" in resposta_bruta: break
                except:
                    break
            
            s.close()
            
            # Converte para string apenas para exibir, tratando erros
            texto_final = resposta_bruta.decode('cp1252', errors='replace')
            self.log_debug(f"Resposta bruta recebida: {texto_final}")

            if "|" in texto_final:
                fatias = [f for f in texto_final.split('#') if "|" in f]
                if fatias:
                    item = fatias[-1].split('|')
                    self.atualizar_tela(item[0].strip(), item[1].strip())
                    return

            self.atualizar_tela("PRODUTO NÃO ENCONTRADO", "---", "orange")
            
        except Exception as e:
            self.log_debug(f"ERRO CRÍTICO: {str(e)}")
            self.atualizar_tela("ERRO DE CONEXÃO", "OFFLINE", "red")

    def atualizar_tela(self, desc, preco, cor_texto="white"):
        self.after(0, self._exibir, desc, preco, cor_texto)

    def _exibir(self, desc, preco, cor_texto):
        self.label.configure(text="BIPE O PRODUTO", text_color="white")
        self.txt_prod.configure(text=desc.upper(), text_color=cor_texto)
        self.txt_price.configure(text=preco)
        self.modal.place(relx=0.5, rely=0.6, anchor="center", width=440, height=280)
        self.after(3500, lambda: self.modal.place_forget())

if __name__ == "__main__":
    app = BuscaPreco()
    app.mainloop()
