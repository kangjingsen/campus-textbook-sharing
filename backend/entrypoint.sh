#!/bin/bash
set -e

echo "Waiting for MySQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "MySQL is ready!"

echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
done
echo "Redis is ready!"

echo "Running migrations..."
python manage.py makemigrations users textbooks orders messaging reviews statistics recommendations --noinput
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Loading initial data..."
python manage.py loaddata initial_data || echo "No initial data fixture found, skipping..."

echo "Creating superuser if not exists..."
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123456', role='superadmin', college='管理学院', major='系统管理')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

echo "Starting Daphne server..."
daphne -b 0.0.0.0 -p 8000 config.asgi:application
