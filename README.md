# Projeto MOM - Contador de palavras-chave (Python + ActiveMQ)

## Executar
`python main.py` -> abre o Cliente. Informe arquivo e palavras-chave (ex.: `java,python,fila`) e clique em Iniciar.
Use "Atraso por linha" (ex.: 20 ms) para ver o dashboard atualizando ao vivo.

## Gerar executável
`pip install pyinstaller` e depois `pyinstaller --onefile main.py` -> `dist/main.exe` (ou `dist/main` no Linux/Mac).

## Mapa com os exemplos do professor
| Exemplo Java    | Aqui          | Papel                                        |
|-----------------|---------------|----------------------------------------------|
| Produtor.java   | leitor.py     | envia cada linha para a FILA                 |
| Consumidor.java | worker.py     | recebe linha da fila e conta palavras        |
| Publisher.java  | worker.py     | publica a contagem no TÓPICO                 |
| Subscriber.java | dashboard.py  | assina o tópico e atualiza a interface       |
| (novo)          | cliente.py    | interface inicial, dispara o workflow        |
