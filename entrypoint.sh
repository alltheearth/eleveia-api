#!/bin/sh
set -e

echo "=========================================="
echo "🟢 EleveIA - Iniciando aplicação"
echo "=========================================="

# Verificar Gunicorn
echo "🔍 Verificando Gunicorn..."
if ! command -v gunicorn >/dev/null 2>&1; then
    echo "❌ ERRO: Gunicorn não está instalado!"
    exit 1
fi
GUNICORN_VERSION=$(gunicorn --version 2>&1 | head -n1)
echo "✅ $GUNICORN_VERSION"

# Aguardar banco
echo "⏳ Aguardando banco de dados..."
sleep 3

# Migrations
echo "🔄 Executando migrações..."
python manage.py migrate --noinput || {
    echo "❌ Erro nas migrações!"
    exit 1
}

# Collectstatic (SEM --clear, COM timeout)
echo "📦 Coletando arquivos estáticos..."
timeout 60 python manage.py collectstatic --noinput || {
    echo "⚠️  Collectstatic demorou demais ou falhou. Continuando..."
}

echo "=========================================="
echo "🚀 Iniciando Gunicorn (porta 8000)"
echo "=========================================="
echo "📍 API: http://0.0.0.0:8000/api/v1/"
echo "📍 Admin: http://0.0.0.0:8000/admin/"
echo "📍 Docs: http://0.0.0.0:8000/api/v1/docs/"
echo "=========================================="

# Iniciar Gunicorn
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info