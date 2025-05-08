import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List


class PostgreSql:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "postgres",
        user: str = "postgres",
        password: str = "postgres",
    ):
        """
        Construtor da classe PostgreSql.
        :param host: Endereço do servidor PostgreSQL.
        :param port: Porta do servidor PostgreSQL.
        :param dbname: Nome do banco de dados.
        :param user: Nome do usuário.
        :param password: Senha do usuário.
        """
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None

    def connect(self):
        """Estabelece a conexão com o banco de dados PostgreSQL."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            print("Conexão com o banco de dados estabelecida com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Conexão com o banco de dados fechada.")

    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executa uma query no banco de dados.
        :param query: A query SQL a ser executada.
        :param params: Parâmetros para a query (opcional).
        :return: Lista de dicionários com os resultados da query.
        """
        try:
            if not self.connection:
                self.connect()

            # Executa a query
            self.cursor.execute(query, params)
            self.connection.commit()  # Realiza o commit

            # Retorna os resultados (se for uma query SELECT)
            if self.cursor.description:
                return self.cursor.fetchall()
            else:
                return []
        except Exception as e:
            print(f"Erro ao executar a query: {e}")
            self.connection.rollback()  # Desfaz a transação em caso de erro
            raise
        finally:
            self.disconnect()

    def query_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Executa uma query a partir de um arquivo.
        :param file_path: Caminho do arquivo contendo a query SQL.
        :return: Lista de dicionários com os resultados da query.
        """
        try:
            with open(file_path, "r") as file:
                query = file.read()
                return self.query(query)
        except Exception as e:
            print(f"Erro ao ler o arquivo ou executar a query: {e}")
            raise


# Exemplo de uso
if __name__ == "__main__":
    # Cria uma instância do banco de dados
    database = PostgreSql(
        host="localhost",
        port=5432,
        dbname="meu_banco",
        user="meu_usuario",
        password="minha_senha",
    )

    # Executa uma query a partir de um arquivo
    try:
        results = database.query_from_file("./provider/c_bp_contractproduct")
        print("Resultados da query:", results)
    except Exception as e:
        print("Erro durante a execução:", e)