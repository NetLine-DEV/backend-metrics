# ...existing content...

## Resetar o banco de dados e criar um superusuário

1. Apague o arquivo do banco de dados atual (`db.sqlite3` ou o banco de dados que você estiver usando).
2. Execute as migrações para recriar o banco de dados:
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Crie um superusuário:
   ```sh
   python manage.py createsuperuser
   ```
   Siga as instruções para definir o email, nome de usuário e senha do superusuário.

# ...existing content...
