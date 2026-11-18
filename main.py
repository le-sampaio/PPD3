"""Ponto de entrada único. Uso:

    python main.py              -> abre o Cliente (padrão)
    python main.py dashboard    -> abre só o Dashboard
    python main.py worker       -> sobe um Worker
    python main.py leitor ...   -> sobe um Leitor

Ter um único ponto de entrada facilita gerar UM executável (.exe) com o PyInstaller.
"""
import sys


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "cliente"
    resto = sys.argv[2:]
    if modo == "cliente":
        import cliente
        cliente.main(resto)
    elif modo == "dashboard":
        import dashboard
        dashboard.main(resto)
    elif modo == "worker":
        import worker
        worker.main(resto)
    elif modo == "leitor":
        import leitor
        leitor.main(resto)
    else:
        print("Modos: cliente | dashboard | worker | leitor")
        sys.exit(1)


if __name__ == "__main__":
    main()
