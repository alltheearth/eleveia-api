#!/bin/sh
set -e

echo "=========================================="
echo "🟢 EleveIA - Iniciando aplicação"
echo "=========================================="

# Verificar Gunicorn
echo "🔍 Verificando Gunicorn..."
gunicorn --version || { echo "❌ Gunicorn não instalado!"; exit 1; }
echo "✅ Gunicorn OK"

# Aguardar banco
echo "⏳ Aguardando banco de dados..."
sleep 3

# Migrations
echo "🔄 Executando migrações..."
python manage.py migrate --noinput || {
    echo "❌ Erro nas migrações!"
    exit 1
}

# Pular collectstatic
echo "⚠️  Pulando collectstatic (usando WhiteNoise)"

echo "=========================================="
echo "🚀 Iniciando Gunicorn (porta 8000)"
echo "=========================================="
echo "📍 API: http://0.0.0.0:8000/api/v1/"
echo "📍 Admin: http://0.0.0.0:8000/admin/"
echo "📍 Docs: http://0.0.0.0:8000/api/v1/docs/"
echo "=========================================="

# ✅ TIMEOUT AUMENTADO PARA 600 SEGUNDOS (10 minutos)
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --timeout 600 \
    --graceful-timeout 600 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info