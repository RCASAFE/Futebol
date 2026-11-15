import os
import psycopg

# CONECTANDO O PYTHON COM O BANCO DE DADOS

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Configure a variável DATABASE_URL.")

print("Tentando conectar ao PostgreSQL...")

conn = psycopg.connect(DATABASE_URL)

print("Conexão com o banco de dados estabelecida.")