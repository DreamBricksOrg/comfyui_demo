# ComfyUI Backend

> Serviço de processamento em fila única (FIFO) para geração de imagens via Stable Diffusion + ComfyUI, com health-check e notificações SMS.

---

## Pré-requisitos

* Python 3.10+
* Docker & Docker Compose (opcional)
* Redis (para dev local ou dentro de container)

---

## 📦 Instalação e execução em modo de desenvolvimento

1. Clone o repositório e entre na pasta:

   ```bash
   git clone git@github.com:seu-org/comfyui-backend.git
   cd comfyui-backend
   ```

2. Crie um virtualenv e instale dependências:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure seu `.env` (veja [exemplo de `.env.example`](./.env.example)).

4. Garanta que um Redis esteja rodando (local ou container). Por exemplo, para dev rápido:

   ```bash
   docker run -d --name redis-local -p 6379:6379 redis:7-alpine
   ```

5. Inicie a aplicação:

  Antes adicione as variáveis de ambiente ao bash onde estiver executando, para ter acesso de desenvolvimento a stack da AWS que está sendo usada.

   ```bash
   $env:AWS_ACCESS_KEY_ID="XXXXXXXXXXXXXX"
   $env:AWS_SECRET_ACCESS_KEY="XXXXXXXXX"
   $env:AWS_REGION="us-east-1"
   # Se AWS_ACCESS_KEY_ID ficar vazio, as imagens serão salvas localmente
   ```

Depois rode assim para debuggar

   ```bash
   uvicorn main:app \
     --app-dir src \
     --host 0.0.0.0 \
     --port 5001 \
     --reload \
     --log-level debug
   ```

  Use log-level info para ambientes de produção, ou stack tracing com Datadog ou Sentry.

---

## 🐳 Execução com Docker

### 1. Criar rede Docker

```bash
docker network create comfyui-net
```

### 2. Levantar o Redis em container

```bash
docker run -d \
  --name redis-local \
  --network comfyui-net \
  -p 6379:6379 \
  redis:7-alpine
```

### 3. Build da sua API

No diretório raiz, execute:

```bash
docker build -t comfyui-api .
```

### 4. Rodar o container da API

```bash
docker run -d \
  --name comfyui-backend \
  --network comfyui-net \
  -p 5000:5000 \
  -e REDIS_URL="redis://redis-local:6379/0" \
  -e BASE_URL="http://localhost:5000" \
  -e AWS_ACCESS_KEY_ID="" \
  -e AWS_SECRET_ACCESS_KEY="" \
  -e AWS_REGION="us-east-1" \
  comfyui-api
```
Caso `AWS_ACCESS_KEY_ID` esteja vazio, as imagens serão mantidas em disco e o armazenamento S3 não será utilizado.

> **Flags principais**
>
> * `--network comfyui-net` — conecta ao Redis pelo DNS interno `redis-local`
> * `-e REDIS_URL` — aponte para `redis://redis-local:6379/0`
> * `-e BASE_URL` — URL pública para callbacks / notificações

Verifique os logs com:

```bash
docker logs -f comfyui-backend
```

Mesmo procedimento no container ECS Blue and Green da AWS

---

## 🛠 Exemplos de endpoints

* **Health-check**

  ```
  GET /alive
  → "Alive"
  ```

* **Fila de upload**

  ```bash
  curl -X POST http://localhost:5000/api/upload \
    -F "image=@/caminho/para/sua.jpg"
  ```

* **Registrar telefone para SMS**

  ```bash
  curl -X POST "http://localhost:5000/api/notify?request_id=<UUID>&phone=+5511999999999"
  ```

* **Consultar resultado**

  ```bash
  curl http://localhost:5000/api/result?request_id=<UUID>
  ```

* **Upload com escolha de workflow**

  ```
  GET  /api/uploadwithworkflow      → formulário HTML para escolher workflow + imagem
  POST /api/uploadwithworkflow      → envia o job (multipart: workflow, image)
  ```

---

## 🚀 Docker Compose (opcional)

Se preferir, crie um `docker-compose.yml`:

```yaml
version: "3.8"
services:
  redis:
    image: redis:7-alpine
    container_name: redis-local
    ports:
      - "6379:6379"

  api:
    build: .
    container_name: comfyui-backend
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis-local:6379/0
      - BASE_URL=http://localhost:5000
    ports:
      - "5000:5000"
    networks:
      - comfyui-net

networks:
  comfyui-net:
    driver: bridge
```

E, então:

```bash
docker-compose up --build
```

---

## ⚙️ Configuração

Todas as variáveis de ambiente ficam no arquivo `.env`. Exemplo mínimo:

```dotenv
BASE_URL=http://localhost:5000
REDIS_URL=redis://localhost:6379/0
COMFYUI_API_SERVER=ec2-xx-xx-xx-xx.compute.amazonaws.com:8188
IMAGE_TEMP_FOLDER=temp
WORKFLOW_PATH=src/workflows/comfyui_basic.json
WORKFLOW_NODE_ID_KSAMPLER=-1
WORKFLOW_NODE_ID_IMAGE_LOAD=3023
WORKFLOW_NODE_ID_TEXT_INPUT=-1
LOG_API=https://meulog.com/logs
LOG_PROJECT_ID=seuprojetoid
SMS_API_URL=https://smsdev.com.br/send
SMS_API_KEY=SEUTOKENAQUI
DEFAULT_PROCESSING_TIME=80
DEBUG_WORKER=false
```

## ⚙️ Worker

O `worker.py` roda em loop (`worker_loop`), a cada 0.5s:

1. `check_for_new_jobs` — move itens de `submissions_queue` para hashes `job:{id}` no Redis.
2. `process_jobs` — varre os jobs em Redis (`queued`, `processing`, `failed`), atualiza progresso estimado, e reenfileira falhas (até 3 tentativas).
3. `activate_queued_jobs` — pega o job mais antigo da fila e dispara em um servidor ComfyUI disponível.

Para rodar o worker:

```bash
python -m worker --app-dir src
# ou, dentro do container:
python src/worker.py
```

### Flag `DEBUG_WORKER`

Por padrão (`DEBUG_WORKER=false`), o worker **não** grava logs verbosos por job a cada ciclo — em vez disso, exibe uma única linha de status que se sobrescreve no terminal (como uma barra de progresso), sem reter texto em memória ou crescer um arquivo de log indefinidamente:

```
[14:23:01] queued=2 processing=1 failed=0 servers_in_use=1
```

Para depuração detalhada (dump de cada job a cada ciclo via `structlog`), defina `DEBUG_WORKER=true` no `.env`. **Atenção:** com o worker rodando por longos períodos e a saída redirecionada para um arquivo, o modo debug pode gerar um arquivo de log muito grande — use apenas para investigação pontual.

## Dummy ComfyUI Server

Para desenvolvimento, você pode rodar um servidor dummy que imita as chamadas usadas pelo backend. Ele recebe uma imagem em `/upload/image`, processa em segundo plano e devolve o mesmo arquivo com o texto "dummy" sobreposto após um atraso configurável (variável `DEFAULT_PROCESSING_TIME`, em milissegundos). Para iniciar:

```bash
uvicorn dummy_comfyui_server:app --app-dir src --port 8188
```

O servidor implementa os endpoints `/prompt`, `/history/{id}`, `/view`, `/queue` e o WebSocket `/ws`.


