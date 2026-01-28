#!/bin/sh
set -e

echo "🟢 Starting Django (Supabase DB)"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
