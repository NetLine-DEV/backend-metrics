#!/bin/bash

# Função para verificar se o PostgreSQL está pronto
wait_for_postgres() {
    echo "Aguardando PostgreSQL..."
    while ! nc -z db 5432; do
        sleep 0.1
    done
    echo "PostgreSQL está pronto!"
}

# Instalando netcat para verificar a conexão com o banco
apt-get update && apt-get install -y netcat-traditional

# Aguardando o PostgreSQL estar pronto
wait_for_postgres

# Aplicando migrações
echo "Aplicando migrações..."
python manage.py migrate

# Criando superusuário (apenas se não existir)
echo "Criando superusuário..."
python manage.py createsuperuser --noinput || true

# Iniciando o Gunicorn
echo "Iniciando Gunicorn..."
exec gunicorn metrics_api.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - 