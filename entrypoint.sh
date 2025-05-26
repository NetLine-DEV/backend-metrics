#!/bin/bash

# Função para verificar se o PostgreSQL está pronto
wait_for_postgres() {
    echo "Aguardando PostgreSQL..."
    while ! nc -z db 5432; do
        sleep 0.1
    done
    echo "PostgreSQL está pronto!"
}

# Aguardando o PostgreSQL estar pronto
wait_for_postgres

# Aplicando migrações
echo "Aplicando migrações..."
python manage.py migrate

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
# Criando superusuário com variáveis do .env (se ainda não existir)
echo "Verificando/criando superusuário..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if username and email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superusuário '{username}' criado.")
    else:
        print(f"Superusuário '{username}' já existe.")
else:
    print("Variáveis de superusuário não definidas. Pulando criação.")
EOF

# Iniciando Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn metrics_api.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile -
