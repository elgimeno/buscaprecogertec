import socket
import customtkinter as ctk
import datetime

# Configurações do Servidor Gertec
IP_SERVIDOR = "192.168.127.5"
PORTA_SERVIDOR = 6500

class AppBuscaPreco(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Consulta de Preços - LJ 27")
        self.geometry("500x550")
        ctk.set_appearance_mode("dark")

        # Layout
        self.label = ctk.CTkLabel(self, text="BIPE O CÓDIGO", font=("Helvetica", 24, "bold"))
        self.label.pack(pady=40)

        self.entry = ctk.CTkEntry(self, width=350, height=50, font=("Consolas", 30), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.consultar)
        self.entry.focus_set()

        # Modal de Resultado (Frame)
        self.modal = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        self.desc_label = ctk.CTkLabel(self.modal, text="", font=("Helvetica", 18, "bold"), text_color="black", wraplength=350)
        self.desc_label.pack(pady=20)
        self.preco_label = ctk.CTkLabel(self.modal, text="", font=("Helvetica", 50, "bold"), text_color="#2563eb")
        self.preco_label.pack(pady=20)

    def consultar(self, event):
        ean = self.entry.get().strip()
        self.entry.delete(0, 'end')

        if not ean: return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((IP_SERVIDOR, PORTA_SERVIDOR))
                
                # Protocolo validado para LJ 27
                s.sendall(b"#ID|01#")
                import time; time.sleep(0.4)
                s.sendall(f"#{ean}#".encode('latin-1'))
                
                resposta = s.recv(1024).decode('latin-1')
                
                if "|" in resposta:
                    dados = resposta.split('#')[-1].split('|')
                    self.exibir_resultado(dados[0], dados[1], ean)
                else:
                    self.exibir_resultado("NÃO ENCONTRADO", "---", ean)
        except:
            self.exibir_resultado("ERRO DE CONEXÃO", "OFFLINE", ean)

    def exibir_resultado(self, desc, preco, ean):
        self.desc_label.configure(text=desc.upper())
        self.preco_label.configure(text=preco)
        self.modal.place(relx=0.5, rely=0.6, anchor="center", width=420, height=280)
        
        # Log de Auditoria
        with open("log_consultas.txt", "a") as f:
            data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            f.write(f"{data} | EAN: {ean} | {desc} | {preco}\n")

        # Fecha sozinho após 2 segundos
        self.after(2000, lambda: self.modal.place_forget())

if __name__ == "__main__":
    app = AppBuscaPreco()
    app.mainloop()
