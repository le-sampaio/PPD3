"""Worker: CONSUMIDOR da fila + PUBLISHER do tópico.

Equivale a Consumidor.java + Publisher.java juntos, mas em loop contínuo.
Pode-se rodar vários workers ao mesmo tempo: o broker distribui as linhas
entre eles (é isso que gera o paralelismo).
"""
import argparse
import json
import os
import re
import time
from collections import Counter

import stomp

import config

PALAVRA = re.compile(r"\w+", re.UNICODE)


class Worker(stomp.ConnectionListener):
    def __init__(self, nome):
        self.nome = nome
        self.conn = None

    def on_message(self, frame):
        """Chamado a cada linha recebida da fila."""
        msg = json.loads(frame.body)
        ocorrencias = Counter(PALAVRA.findall(msg["texto"].lower()))
        contagem = {k: ocorrencias.get(k, 0) for k in msg["keywords"]}

        # Publica o resultado no tópico (Publisher)
        self.conn.send(destination=config.TOPICO,
                       body=json.dumps({"tipo": "contagem", "worker": self.nome,
                                        "linha": msg["linha"], "contagem": contagem}))
        # Só confirma depois de publicar: se o worker cair, a linha volta para a fila
        self.conn.ack(frame.headers["message-id"], frame.headers["subscription"])
        print(f"[{self.nome}] linha {msg['linha']}: {contagem}", flush=True)

    def on_error(self, frame):
        print("Erro do broker:", frame.body, flush=True)


def main(argv=None):
    argparse.ArgumentParser().parse_args(argv)
    worker = Worker(f"worker-{os.getpid()}")
    conn = config.conectar(worker)
    worker.conn = conn

    # prefetchSize=1: o broker entrega 1 linha por vez a cada worker.
    # Sem isso, um único worker poderia "pegar" centenas de linhas de uma vez.
    conn.subscribe(destination=config.FILA, id=1, ack="client-individual",
                   headers={"activemq.prefetchSize": "1"})
    print(f"[{worker.nome}] aguardando linhas...", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        conn.disconnect()


if __name__ == "__main__":
    main()
