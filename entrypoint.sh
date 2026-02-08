#!/bin/bash
set -e

echo "🟢 Starting Django (Supabase DB)"

# Executar migrações
echo "🔄 Executando migrações..."
python manage.py migrate --no-input

# Coletar arquivos estáticos
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "🚀 Iniciando Gunicorn..."

# Executar comando passado (CMD do Dockerfile)
exec "$@"