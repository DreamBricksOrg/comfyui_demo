# Usa a imagem do frontend como stage
FROM node:22-alpine AS frontend
WORKDIR /frontend/db_AI_presentation_react
COPY src/frontend/db_AI_presentation_react/ ./
RUN yarn install && yarn build

# Base image
FROM python:3.10-slim

# Evita buffers em logs
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências compiladas (caso o matplotlib precise)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libjpeg-dev \
      zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia e instala dependências via pip
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para /app
COPY . .

COPY --from=frontend /frontend/dist /app/src/frontend/dist

# Expõe a porta usada pelo Uvicorn
EXPOSE 5000

# Comando padrão para rodar o servidor FastAPI
CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "5000", "--log-level", "info"]