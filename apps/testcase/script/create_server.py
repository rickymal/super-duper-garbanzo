import psycopg2

def setup_source():
    conn = psycopg2.connect(
        dbname="sourcedb",
        user="admin",
        password="admin",
        host="localhost",
        port=5433
    )

    with conn:
        with conn.cursor() as cur:
            print("Criando tabelas...")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS pagamentos (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    valor NUMERIC(10, 2),
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            print("Inserindo dados em 'usuarios'...")
            cur.executemany(
                "INSERT INTO usuarios (nome, email) VALUES (%s, %s);",
                [
                    ("João", "joao@example.com"),
                    ("Maria", "maria@example.com"),
                    ("Henrique", "henrique@example.com"),
                ]
            )

            print("Inserindo dados em 'pagamentos'...")
            cur.executemany(
                "INSERT INTO pagamentos (usuario_id, valor) VALUES (%s, %s);",
                [
                    (1, 100.50),
                    (2, 200.75),
                    (3, 300.00),
                ]
            )

    conn.close()
    print("✅ Tabelas criadas e dados inseridos com sucesso no banco de origem.")

if __name__ == "__main__":
    setup_source()
