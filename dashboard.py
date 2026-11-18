"""Dashboard: SUBSCRIBER do tópico - equivale ao Subscriber.java.

O listener do STOMP roda em outra thread, e o Tkinter só pode ser mexido pela
thread principal. Por isso o listener coloca as mensagens numa queue.Queue e a
interface lê essa fila a cada 100 ms (root.after).
"""
import argparse
import json
import queue
import tkinter as tk
from tkinter import messagebox, ttk

import stomp

import config


class Ouvinte(stomp.ConnectionListener):
    def __init__(self, fila_ui):
        self.fila_ui = fila_ui

    def on_message(self, frame):
        self.fila_ui.put(json.loads(frame.body))


class Dashboard:
    def __init__(self, keywords):
        self.fila_ui = queue.Queue()
        self.totais = {}
        self.por_worker = {}
        self.processadas = 0
        self.enviadas = {}      # "par"/"impar" -> linhas enviadas

        self.root = tk.Tk()
        self.root.title("Dashboard - Contagem de Palavras")
        self.root.geometry("460x520")
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        self.lbl_status = ttk.Label(frm, text="Aguardando mensagens...",
                                    font=("Segoe UI", 12, "bold"))
        self.lbl_status.pack(anchor="w")
        self.lbl_linhas = ttk.Label(frm, text="Linhas processadas: 0")
        self.lbl_linhas.pack(anchor="w", pady=(2, 8))

        ttk.Label(frm, text="Ocorrências por palavra-chave").pack(anchor="w")
        self.tree = ttk.Treeview(frm, columns=("palavra", "qtd"), show="headings", height=10)
        self.tree.heading("palavra", text="Palavra")
        self.tree.heading("qtd", text="Quantidade")
        self.tree.column("qtd", width=110, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=(0, 8))

        ttk.Label(frm, text="Linhas processadas por worker").pack(anchor="w")
        self.tree_w = ttk.Treeview(frm, columns=("worker", "linhas"), show="headings", height=5)
        self.tree_w.heading("worker", text="Worker")
        self.tree_w.heading("linhas", text="Linhas")
        self.tree_w.column("linhas", width=110, anchor="e")
        self.tree_w.pack(fill="both", expand=True)

        for k in keywords:
            self._garantir_linha(k)

    def _garantir_linha(self, palavra):
        if palavra not in self.totais:
            self.totais[palavra] = 0
            self.tree.insert("", "end", iid=palavra, values=(palavra, 0))

    def tratar(self, msg):
        if msg["tipo"] == "contagem":
            for palavra, qtd in msg["contagem"].items():
                self._garantir_linha(palavra)
                self.totais[palavra] += qtd
                self.tree.set(palavra, "qtd", self.totais[palavra])
            self.processadas += 1
            w = msg["worker"]
            if w not in self.por_worker:
                self.por_worker[w] = 0
                self.tree_w.insert("", "end", iid=w, values=(w, 0))
            self.por_worker[w] += 1
            self.tree_w.set(w, "linhas", self.por_worker[w])
        elif msg["tipo"] == "leitor_fim":
            self.enviadas[msg["leitor"]] = msg["linhas"]

        total_env = sum(self.enviadas.values())
        self.lbl_linhas.config(
            text=f"Linhas processadas: {self.processadas}"
                 f"   |   enviadas: {total_env}   |   leitores concluídos: {len(self.enviadas)}/2")
        if len(self.enviadas) == 2 and self.processadas >= total_env:
            self.lbl_status.config(text="Concluído")
        else:
            self.lbl_status.config(text="Processando...")

    def atualizar(self):
        try:
            while True:
                self.tratar(self.fila_ui.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self.atualizar)

    def executar(self):
        try:
            self.conn = config.conectar(Ouvinte(self.fila_ui))
            self.conn.subscribe(destination=config.TOPICO, id=2, ack="auto")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível conectar ao ActiveMQ:\n{e}")
            return
        self.root.after(100, self.atualizar)
        self.root.mainloop()
        try:
            self.conn.disconnect()
        except Exception:
            pass


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--keywords", default="")
    a = p.parse_args(argv)
    kws = [k.strip().lower() for k in a.keywords.split(",") if k.strip()]
    Dashboard(kws).executar()


if __name__ == "__main__":
    main()
