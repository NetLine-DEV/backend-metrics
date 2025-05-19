# Usando a imagem base do Python 3.12.2
FROM python:3.12.2

# Definindo variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=metrics_api.settings

# Criando e definindo o diretório de trabalho
WORKDIR /metrics_api

# Instalando as dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiando os arquivos de requisitos
COPY requirements.txt .

# Instalando as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiando o arquivo .env primeiro
COPY .env .

# Copiando o projeto
COPY . .

# Criando diretório para arquivos estáticos
RUN mkdir -p staticfiles

# Coletando arquivos estáticos
RUN python manage.py collectstatic --noinput

# Aplicando migrações
RUN python manage.py migrate

# Criando o superusuário (apenas se não existir)
RUN python manage.py createsuperuser --noinput || true

# Expondo a porta 8000
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["gunicorn", "metrics_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-"]