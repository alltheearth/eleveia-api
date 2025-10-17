# Etapa base
FROM python:3.11-slim

# Diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala o Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copia os arquivos de dependência
COPY pyproject.toml poetry.lock* README.md /app/

# Instala dependências com poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copia o restante do projeto
COPY . /app/

# Expõe a porta da aplicação
EXPOSE 8000

# Comando padrão para rodar o servidor
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]poetry 