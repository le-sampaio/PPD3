"""Leitor de linhas (PRODUTOR da fila) - equivale ao Produtor.java.

Lê o arquivo e envia para a fila apenas as linhas pares OU apenas as ímpares
(numeração começando em 1). Dois processos deste programa são iniciados pelo
Cliente: um com --paridade par e outro com --paridade impar.
"""
import argparse
import json
import time

import config


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--arquivo", required=True)
    p.add_argument("--paridade", choices=["par", "impar"], required=True)
    p.add_argument("--keywords", required=True, help="palavras separadas por vírgula")
    p.add_argument("--delay", type=float, default=0, help="atraso por linha (ms)")
    a = p.parse_args(argv)

    keywords = [k.strip().lower() for k in a.keywords.split(",") if k.strip()]
    resto = 0 if a.paridade == "par" else 1

    conn = config.conectar()
    enviadas = 0

    with open(a.arquivo, encoding="utf-8", errors="replace") as f:
        for n, linha in enumerate(f, start=1):   # lê uma linha por vez (arquivo grande)
            if n % 2 != resto:
                continue
            msg = {"linha": n, "texto": linha.rstrip("\n"), "keywords": keywords}
            conn.send(destination=config.FILA, body=json.dumps(msg),
                      content_type="application/json")
            enviadas += 1
            if a.delay:
                time.sleep(a.delay / 1000)

    # Avisa o dashboard quantas linhas este leitor enviou, para ele saber
    # quando todas as linhas já foram contadas.
    conn.send(destination=config.TOPICO,
              body=json.dumps({"tipo": "leitor_fim", "leitor": a.paridade,
                               "linhas": enviadas}))
    conn.disconnect()
    print(f"[leitor {a.paridade}] terminou: {enviadas} linhas enviadas")


if __name__ == "__main__":
    main()
