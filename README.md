# Projeto MOM - Contagem Paralela de Palavras-Chave

**Disciplina:** Programação Paralela e Distribuída (2026.2) - IFCE, Engenharia de Computação
**Professor:** Cidcley T. de Souza

Workflow de computação paralela que conta palavras-chave em um arquivo de texto grande,
usando **MOM (Message-Oriented Middleware)** com **Apache ActiveMQ**.
Implementado em **Python**, comunicando-se com o broker pelo protocolo **STOMP**.

---

## 1. Visão geral da arquitetura

```
                       +--> Leitor (linhas PARES)   --+
 Cliente (interface) --|                              |--> FILA --> Worker 1 --+
  (pede arquivo e      +--> Leitor (linhas ÍMPARES) --+   (Queue)   Worker 2 --+--> TÓPICO --> Dashboard
   palavras-chave)                                                  Worker N --+    (Topic)     (interface)
                           [Produtor]                    [Consumidor + Publisher]                [Subscriber]
```

| Etapa do enunciado | Componente | Arquivo | Papel no MOM |
|---|---|---|---|
| (1) Cliente | Interface inicial | `cliente.py` | Dispara os demais processos |
| (2) Leitores de linha | Pares e ímpares | `leitor.py` | **Produtor** da fila |
| (3) Fila do broker | `/queue/FILA_LINHAS` | ActiveMQ | Distribui cada linha para **um** worker |
| (4) Workers | Contadores | `worker.py` | **Consumidor** da fila + **Publisher** do tópico |
| (5) Tópico do broker | `/topic/TOPICO_CONTAGEM` | ActiveMQ | Entrega cada resultado a **todos** os assinantes |
| (6) Dashboard | Interface de resultados | `dashboard.py` | **Subscriber** do tópico |

---

## 2. Como a comunicação acontece

**Fila (Queue) - modelo ponto a ponto.** Cada linha enviada pelos leitores é entregue a
apenas **um** worker. Com vários workers rodando ao mesmo tempo, o broker divide as linhas
entre eles, e isso é o paralelismo do trabalho.

**Tópico (Topic) - modelo publish/subscribe.** Cada resultado publicado pelos workers é
entregue a **todos** os assinantes do tópico (aqui, o dashboard).

### Passo a passo

1. `cliente.py` abre o **Dashboard**, depois os **Workers**, depois os **2 Leitores**, cada um como
   processo separado (`subprocess.Popen`). Os componentes só se comunicam pelo broker.
   O dashboard sobe primeiro porque o tópico não guarda mensagens para quem ainda não assinou.
2. Cada **leitor** (`leitor.py`) lê o arquivo linha a linha e envia à fila (`conn.send`) apenas as
   linhas da sua paridade (pares ou ímpares, numeração a partir de 1).
3. Cada **worker** (`worker.py`) está inscrito na fila (`conn.subscribe`). A cada linha recebida
   (`on_message`), conta as palavras-chave e publica o resultado no tópico (`conn.send`).
   Só depois confirma o recebimento ao broker (`conn.ack`).
4. O **dashboard** (`dashboard.py`) está inscrito no tópico, soma as contagens por palavra e
   atualiza a interface.
5. Ao terminar, cada leitor publica no tópico uma mensagem `leitor_fim` com o total de linhas
   enviadas. Quando os dois leitores terminaram e o número de linhas processadas é igual ao
   número de linhas enviadas, o dashboard mostra **"Concluído"**.

### Formato das mensagens (JSON)

Leitor -> Fila:
```json
{"linha": 42, "texto": "texto da linha", "keywords": ["java", "fila"]}
```
Worker -> Tópico:
```json
{"tipo": "contagem", "worker": "worker-1234", "linha": 42, "contagem": {"java": 2, "fila": 0}}
```
Leitor -> Tópico (fim da leitura):
```json
{"tipo": "leitor_fim", "leitor": "par", "linhas": 25000}
```

---

## 3. Decisões de projeto

- **`ack="client-individual"`**: o worker só confirma a linha depois de publicar o resultado.
  Se ele falhar no meio, a linha volta para a fila e outro worker a processa, sem perder dados.
- **`activemq.prefetchSize = 1`**: o broker entrega uma linha por vez a cada worker, o que
  distribui a carga de forma justa. Sem isso, um worker poderia receber muitas linhas de uma vez.
- **Processos separados**: leitores, workers e dashboard são processos independentes, como o
  enunciado pede ("execuções" distintas), e podem rodar até em máquinas diferentes
  (variáveis `MOM_HOST` e `MOM_PORT`).
- **`queue.Queue` no dashboard**: o listener do STOMP roda em outra thread, e o Tkinter só pode
  ser atualizado pela thread principal. As mensagens passam por uma `Queue` e a interface a lê
  a cada 100 ms.
---

## 4. Requisitos

- **Java 17** (para o ActiveMQ)
- **Apache ActiveMQ Classic** - https://activemq.apache.org/components/classic/download
- **Python 3.9+** (com Tkinter, que já vem no instalador do Windows)
- Biblioteca `stomp.py`: `pip install -r requirements.txt`

## 5. Como executar

1. **Subir o broker** (na pasta do ActiveMQ):
   ```
   bin\activemq start
   ```
   Painel de administração: http://localhost:8161/admin (usuário e senha: `admin`).
   Porta STOMP: 61613.
2. **Instalar a dependência:**
   ```
   pip install -r requirements.txt
   ```
3. **(Opcional) gerar um arquivo de teste:**
   ```
   python gerar_arquivo_teste.py 50000
   ```
   Cria `entrada.txt` com 50.000 linhas.
4. **Executar o Cliente:**
   ```
   python main.py
   ```
5. Na janela do Cliente: escolha o arquivo, informe as palavras-chave separadas por vírgula
   (ex.: `java,python,fila`), defina o número de workers e clique em **Iniciar**.
   O campo "Atraso por linha" (ex.: 20 ms) deixa a atualização do dashboard visível.
6. Para encerrar, use **Encerrar tudo** no Cliente.

## 6. Estrutura do projeto

```
main.py                  ponto de entrada (abre o cliente, ou dashboard/worker/leitor)
cliente.py               interface do cliente; inicia dashboard, workers e leitores
leitor.py                produtor: envia linhas pares ou ímpares para a fila
worker.py                consome a fila, conta palavras-chave e publica no tópico
dashboard.py             subscriber do tópico; mostra as contagens em tempo real
config.py                host, porta, nomes da fila e do tópico, função de conexão
gerar_arquivo_teste.py   gera um arquivo de texto grande para testes
requirements.txt         dependências Python
```

## 7. Configuração do broker

Por padrão o programa conecta em `localhost:61613` com usuário e senha `admin`/`admin`.
Para mudar, defina as variáveis de ambiente `MOM_HOST`, `MOM_PORT`, `MOM_USER` e `MOM_PASS`.
