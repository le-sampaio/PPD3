"""Configuração comum a todos os programas.

O ActiveMQ expõe vários protocolos. Os exemplos Java do professor usam
OpenWire (porta 61616). Em Python usamos STOMP (porta 61613), que já vem
habilitado por padrão no ActiveMQ Classic. O broker é o mesmo.
"""
import os

import stomp

HOST = os.environ.get("MOM_HOST", "localhost")
PORT = int(os.environ.get("MOM_PORT", "61613"))
USUARIO = os.environ.get("MOM_USER", "admin")
SENHA = os.environ.get("MOM_PASS", "admin")

# Equivalentes ao "FILA_EXEMPLO" e "TOPICO_EXEMPLO" do professor
FILA = "/queue/FILA_LINHAS"          # leitores -> workers (cada linha vai para UM worker)
TOPICO = "/topic/TOPICO_CONTAGEM"    # workers -> dashboard (todos os assinantes recebem)


def conectar(listener=None):
    """Abre a conexão com o broker (equivale a createConnection + start do Java)."""
    conn = stomp.Connection([(HOST, PORT)], heartbeats=(0, 0))
    if listener is not None:
        conn.set_listener("", listener)
    conn.connect(USUARIO, SENHA, wait=True)
    return conn
