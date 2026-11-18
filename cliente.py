"""Cliente: pede o arquivo e as palavras-chave e dispara todo o workflow.

Ordem de inicialização:
  1) Dashboard (precisa estar inscrito no tópico antes de chegarem resultados,
     pois tópico não guarda mensagens para quem ainda não assinou)
  2) Workers
  3) Os 2 leitores (linhas pares e ímpares)
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import config

DIR = os.path.dirname(os.path.abspath(__file__))


def comando(modo, *args):
    """Monta o comando para abrir outro módulo (funciona também dentro do .exe)."""
    if getattr(sys, "frozen", False):
        base = [sys.executable]
    else:
        base = [sys.executable, os.path.join(DIR, "main.py")]
    return base + [modo, *args]


class Cliente:
    def __init__(self, root):
        self.root = root
        self.processos = []
        root.title("Cliente - Contador de Palavras (MOM)")
        root.geometry("640x470")
        root.protocol("WM_DELETE_WINDOW", self.fechar)

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        self.var_arquivo = tk.StringVar()
        self.var_kw = tk.StringVar()
        self.var_workers = tk.IntVar(value=3)
        self.var_delay = tk.IntVar(value=0)

        ttk.Label(frm, text="Arquivo de entrada:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_arquivo).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(frm, text="Procurar...", command=self.escolher).grid(row=0, column=2)

        ttk.Label(frm, text="Palavras-chave (vírgula):").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.var_kw).grid(row=1, column=1, columnspan=2,
                                                      sticky="ew", padx=6)

        ttk.Label(frm, text="Nº de workers:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Spinbox(frm, from_=1, to=10, textvariable=self.var_workers,
                    width=6).grid(row=2, column=1, sticky="w", padx=6)

        ttk.Label(frm, text="Atraso por linha (ms):").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Spinbox(frm, from_=0, to=2000, textvariable=self.var_delay,
                    width=6).grid(row=3, column=1, sticky="w", padx=6)

        botoes = ttk.Frame(frm)
        botoes.grid(row=4, column=0, columnspan=3, pady=10, sticky="w")
        ttk.Button(botoes, text="Iniciar", command=self.iniciar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Encerrar tudo", command=self.parar).pack(side="left")

        self.log = scrolledtext.ScrolledText(frm, height=12, state="disabled")
        self.log.grid(row=5, column=0, columnspan=3, sticky="nsew")
        frm.rowconfigure(5, weight=1)

    def escrever(self, texto):
        self.log.config(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def escolher(self):
        caminho = filedialog.askopenfilename(title="Escolha o arquivo de texto")
        if caminho:
            self.var_arquivo.set(caminho)

    def lancar(self, descricao, modo, *args):
        self.processos.append(subprocess.Popen(comando(modo, *args)))
        self.escrever(f"Iniciado: {descricao}")

    def iniciar(self):
        arquivo = self.var_arquivo.get().strip()
        kws = [k.strip() for k in self.var_kw.get().split(",") if k.strip()]
        if not os.path.isfile(arquivo):
            messagebox.showerror("Erro", "Selecione um arquivo válido.")
            return
        if not kws:
            messagebox.showerror("Erro", "Informe ao menos uma palavra-chave.")
            return
        try:                                   # testa se o broker está no ar
            config.conectar().disconnect()
        except Exception as e:
            messagebox.showerror("Erro", f"ActiveMQ não respondeu em "
                                         f"{config.HOST}:{config.PORT}\n{e}")
            return

        self.parar()
        kwstr = ",".join(kws)
        self.lancar("Dashboard", "dashboard", "--keywords", kwstr)
        # espera o dashboard assinar o tópico antes de iniciar o resto
        self.root.after(1500, lambda: self.iniciar_resto(arquivo, kwstr))

    def iniciar_resto(self, arquivo, kwstr):
        for i in range(self.var_workers.get()):
            self.lancar(f"Worker {i + 1}", "worker")
        self.root.after(1000, lambda: self.iniciar_leitores(arquivo, kwstr))

    def iniciar_leitores(self, arquivo, kwstr):
        for paridade in ("par", "impar"):
            self.lancar(f"Leitor de linhas {paridade}es" if paridade == "par"
                        else "Leitor de linhas ímpares",
                        "leitor", "--arquivo", arquivo, "--paridade", paridade,
                        "--keywords", kwstr, "--delay", str(self.var_delay.get()))

    def parar(self):
        for p in self.processos:
            if p.poll() is None:
                p.terminate()
        if self.processos:
            self.escrever("Processos encerrados.")
        self.processos = []

    def fechar(self):
        self.parar()
        self.root.destroy()


def main(argv=None):
    root = tk.Tk()
    Cliente(root)
    root.mainloop()


if __name__ == "__main__":
    main()
