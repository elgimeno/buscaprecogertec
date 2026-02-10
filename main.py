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
        self.txt_prod = ctk.CTkLabel(self.modal, text="", font=("Arial", 18, "bold"), wraplength=380)
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
            
            # 1. Handshake Identêntico ao PowerShell
            s.sendall("#ID|01#".encode('cp1252'))
            time.sleep(0.6) 

            # 2. Envio do Código
            s.sendall(f"#{ean}#".encode('cp1252'))
            
            # 3. Leitura Acumulada Agressiva
            resposta_bruta = ""
            timeout_leitura = time.time() + 4 # 4 segundos para o servidor responder
            
            while time.time() < timeout_leitura:
                try:
                    s.setblocking(False) # Não trava se não houver nada no buffer
                    import select
                    pronto = select.select([s], [], [], 0.5)
                    if pronto[0]:
                        parte = s.recv(4096).decode('cp1252', errors='ignore')
                        if not parte: break
                        resposta_bruta += parte
                        # Se achou o preço, encerra o loop imediatamente
                        if "|" in resposta_bruta: break
                    else:
                        # Se já temos algo e o servidor parou de mandar, processamos
                        if resposta_bruta: break 
                except:
                    break
            
            s.close()

            # 4. Tratamento do Resultado com Fallback
            if "|" in resposta_bruta:
                # Limpa os #live? e pega a parte do preço
                fatias = [f for f in resposta_bruta.split('#') if "|" in f]
                item = fatias[-1].split('|')
                self.atualizar_tela(item[0].strip(), item[1].strip())
            elif "live?" in resposta_bruta:
                self.atualizar_tela("SERVIDOR BUSY (LIVE?)", "TENTE DE NOVO", "orange")
            else:
                self.atualizar_tela("PRODUTO NÃO CADASTRADO", "---", "orange")

        except Exception as e:
            self.atualizar_tela("ERRO DE CONEXÃO", "OFFLINE", "red")

    def atualizar_tela(self, desc, preco, cor_texto="white"):
        self.after(0, self._exibir, desc, preco, cor_texto)

    def _exibir(self, desc, preco, cor_texto):
        self.label.configure(text="BIPE O PRODUTO", text_color="white")
        self.txt_prod.configure(text=desc.upper(), text_color=cor_texto)
        self.txt_price.configure(text=preco)
        self.modal.place(relx=0.5, rely=0.6, anchor="center", width=440, height=280)
        self.after(3000, lambda: self.modal.place_forget())

if __name__ == "__main__":
    app = BuscaPreco()
    app.mainloop()
