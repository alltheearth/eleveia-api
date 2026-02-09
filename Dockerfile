FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

WORKDIR /app

# Instalar dependências do sistema (✅ incluindo coreutils para timeout)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock* README.md ./

# Instalar dependências Python
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Verificar gunicorn
RUN python -c "import gunicorn; print(f'✅ Gunicorn {gunicorn.__version__} instalado')"

# Copiar código
COPY . .

# Criar diretórios
RUN mkdir -p /app/staticfiles /app/media /app/logs

EXPOSE 8000

# Copiar entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]