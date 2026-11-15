
from banco_dados.bd_conn import conn
from werkzeug.security import generate_password_hash, check_password_hash

#Usados para "esconder" a senha de pessoas com acesso ao banco(eu kk)

# CRIAR TABELAS
def criar_tabelas():
    try:
        with conn.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) UNIQUE NOT NULL,
                    senha_hash VARCHAR(255) NOT NULL
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS placar (
                    id SERIAL PRIMARY KEY,

                    id_usuarios INT UNIQUE NOT NULL
                        REFERENCES usuarios(id)
                        ON DELETE CASCADE,

                    gols INT NOT NULL DEFAULT 0
                        CHECK (gols >= 0),

                    assistencias INT NOT NULL DEFAULT 0
                        CHECK (assistencias >= 0),

                    jogos INT NOT NULL DEFAULT 0
                        CHECK (jogos >= 0),

                    media_gols NUMERIC(6,2)
                        GENERATED ALWAYS AS (
                            gols::NUMERIC / NULLIF(jogos, 0)
                        ) STORED
                )
            """)#Defaut é para dizer que se nenhum valor ser informado ele começa pelo zero,
            #o Check é para ver se ele é maior ou igual a 0, 
            #O NUMERIC(6,2) é para um numero maximo, sendo ele 999999,99 e com um numero de casas maximo, sendo ela 0,00
            #O NUMERIC / NULLIF(jogos, 0) faz com que se jogos serem 0, a média sempre será 0(NULL)
            # O STORED faz o banco de dados guardar esse resultado
            # O GENERATED ALWAYS AS faz o numero ser gerado automaticamente 
 
            conn.commit()

    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()


def cadastro_usuario(nome, senha):
    try:
        if not nome or not senha:
            return None

        senha_hash = generate_password_hash(senha)

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO usuarios (nome, senha_hash)
                VALUES (%s, %s)
                RETURNING id
            """, (nome, senha_hash))

            dados = cur.fetchone()
            id_usuario = dados[0]

            cur.execute("""
                INSERT INTO placar (id_usuarios)
                VALUES (%s)
            """, (id_usuario,))

            conn.commit()

            return id_usuario

    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        conn.rollback()
        return None


# LOGIN
def logando(nome, senha):
    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, senha_hash
                FROM usuarios
                WHERE nome = %s
            """, (nome,))

            usuario = cur.fetchone()

            print("Usuário encontrado:", usuario is not None)

            if usuario:
                senha_correta = check_password_hash(usuario[1], senha)
                print("Senha confere:", senha_correta)

                if senha_correta:
                    return usuario[0]

            return None

    except Exception as e:
        print(f"Erro no login: {e}")
        return None


def adicionar_dados(id_usuario, gols, assistencias, jogos=1):
    try:
        if min(gols, assistencias, jogos) < 0:
            raise ValueError("As estatísticas não podem ser negativas.")

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO placar (
                    id_usuarios,
                    gols,
                    assistencias,
                    jogos
                )
                VALUES (%s, %s, %s, %s)

                ON CONFLICT (id_usuarios)
                DO UPDATE SET
                    gols = placar.gols + EXCLUDED.gols,

                    assistencias =
                        placar.assistencias + EXCLUDED.assistencias,

                    jogos = placar.jogos + EXCLUDED.jogos

            """, (id_usuario, gols, assistencias, jogos))
#Da linha 128 a 137 é ele evitando um conflito, porque quando se tenta colocar soma de dados da conflito,
#Ai o Excluded.gols é o que seria excluido(os dados novos), assim em baixo ele soma eles com os que já tem
            conn.commit()
            return True
    except Exception as e:
        print(f"Erro ao atualizar placar: {e}")
        conn.rollback()
        return False

# CONSULTAR RANKING
def tabela():
    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    u.nome,
                    p.gols,
                    p.assistencias,
                    p.jogos,
                    p.media_gols

                FROM placar p

                INNER JOIN usuarios u
                    ON p.id_usuarios = u.id

                ORDER BY
                    p.media_gols DESC NULLS LAST,
                    p.gols DESC
            """)

            return cur.fetchall()

    except Exception as e:
        print(f"Erro ao consultar ranking: {e}")
        return []


def deletar(id):
    with conn.cursor() as cur:
        cur.execute("""
                    DELETE usuarios WHERE id = %s
                    """, (id))