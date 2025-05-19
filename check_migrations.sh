#!/bin/bash

# Verifica se existem migrações pendentes
python manage.py makemigrations --check

# Se o comando anterior retornar 0, não há migrações pendentes
if [ $? -eq 0 ]; then
    echo "Todas as migrações estão criadas!"
    exit 0
else
    echo "ERRO: Existem migrações pendentes!"
    echo "Execute 'python manage.py makemigrations' antes de fazer o build"
    exit 1
fi 