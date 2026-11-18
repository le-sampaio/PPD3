"""Gera um arquivo de texto grande para testar.  Uso: python gerar_arquivo_teste.py [linhas]"""
import random
import sys

VOCAB = ("java python mensagem fila topico broker produtor consumidor "
         "paralelo distribuido thread processo rede servidor cliente dados "
         "sistema codigo teste projeto").split()

n = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
random.seed(1)
with open("entrada.txt", "w", encoding="utf-8") as f:
    for _ in range(n):
        f.write(" ".join(random.choices(VOCAB, k=random.randint(5, 15))) + "\n")
print(f"entrada.txt gerado com {n} linhas")
