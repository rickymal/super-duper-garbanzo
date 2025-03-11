import psycopg2
from collections import defaultdict, deque


def get_all_tables(connection):
    """
    Retorna a lista de todas as tabelas do esquema "public".

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.

    Returns:
        list: Lista com os nomes de todas as tabelas do esquema "public".
    """
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public';
    """
    cursor = connection.cursor()
    cursor.execute(query)
    all_tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return all_tables


def get_table_data_preview(connection, table_name, limit=1000):
    """
    Retorna as colunas e os primeiros valores das primeiras 1000 linhas de uma tabela.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar.
        limit (int): Limite de linhas a serem retornadas.

    Returns:
        dict: Um dicionário onde as chaves são os nomes das colunas e os valores são listas contendo os valores distintos.
    """
    query = f"SELECT * FROM {table_name} LIMIT {limit};"
    cursor = connection.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    data_preview = {column: set() for column in columns}
    for row in rows:
        for idx, value in enumerate(row):
            data_preview[columns[idx]].add(value)

    # Converter os sets para listas para facilitar a manipulação posterior
    data_preview = {column: list(values) for column, values in data_preview.items()}

    cursor.close()
    return data_preview


def get_table_connections(connection, table_name):
    """
    Retorna as tabelas que estão conectadas a uma tabela, assim como as colunas de ligação.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar as conexões.

    Returns:
        dict: Um dicionário com duas listas: "connected_from" e "connected_to", incluindo as chaves primárias e estrangeiras.
    """
    query = """
    SELECT 
        tc.table_name AS source_table, 
        kcu.column_name AS source_column, 
        ccu.table_name AS target_table, 
        ccu.column_name AS target_column 
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu 
            ON tc.constraint_name = kcu.constraint_name 
            AND tc.table_schema = kcu.table_schema 
        JOIN information_schema.constraint_column_usage AS ccu 
            ON ccu.constraint_name = tc.constraint_name 
            AND ccu.table_schema = tc.table_schema 
    WHERE 
        tc.constraint_type = 'FOREIGN KEY';
    """
    cursor = connection.cursor()
    cursor.execute(query)
    connections = {
        "connected_from": [],
        "connected_to": []
    }

    for source_table, source_column, target_table, target_column in cursor.fetchall():
        if source_table == table_name:
            connections["connected_to"].append({
                "target_table": target_table,
                "foreign_key": source_column,
                "primary_key": target_column
            })
        if target_table == table_name:
            connections["connected_from"].append({
                "source_table": source_table,
                "foreign_key": source_column,
                "primary_key": target_column
            })

    cursor.close()
    return connections

from collections import defaultdict

def get_table_dependencies(connection):
    """
    Mapeia as tabelas no banco de dados e suas dependências com informações
    de qual coluna em source_table se conecta a qual coluna em target_table.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.

    Returns:
        dict: Dicionário onde cada chave é o nome da tabela de origem (source_table).
              O valor é outro dicionário em que cada chave é a tabela de destino (target_table),
              e o valor final é uma lista de tuplas (source_column, target_column).
              Exemplo:
              {
                  'tabela_a': {
                      'tabela_b': [('coluna_a', 'coluna_b')],
                      'tabela_c': [('outra_coluna', 'coluna_x')]
                  },
                  ...
              }
    """
    query = """
    SELECT 
        tc.table_name AS source_table, 
        kcu.column_name AS source_column, 
        ccu.table_name AS target_table, 
        ccu.column_name AS target_column 
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu 
            ON tc.constraint_name = kcu.constraint_name 
            AND tc.table_schema = kcu.table_schema 
        JOIN information_schema.constraint_column_usage AS ccu 
            ON ccu.constraint_name = tc.constraint_name 
            AND ccu.table_schema = tc.table_schema 
    WHERE 
        tc.constraint_type = 'FOREIGN KEY';
    """

    cursor = connection.cursor()
    cursor.execute(query)

    # Vamos criar uma estrutura 2 níveis de dicionário:
    # dependencies[source_table][target_table] = [(source_column, target_column), ...]
    dependencies = defaultdict(lambda: defaultdict(list))

    for source_table, source_column, target_table, target_column in cursor.fetchall():
        dependencies[source_table][target_table].append((source_column, target_column))

    cursor.close()
    return dependencies



def topological_sort(dependency_graph):
    """
    Ordena as tabelas com base na dependência utilizando ordenação topológica.

    Args:
        dependency_graph (dict): Dicionário de dependências entre as tabelas.

    Returns:
        list: Lista de tabelas ordenadas de forma que as tabelas menos dependentes estejam primeiro.
    """
    in_degree = {table: 0 for table in dependency_graph}

    for dependencies in dependency_graph.values():
        for dependent_table in dependencies:
            in_degree[dependent_table] += 1

    queue = deque([table for table, degree in in_degree.items() if degree == 0])
    sorted_tables = []

    while queue:
        table = queue.popleft()
        sorted_tables.append(table)
        for dependent_table in dependency_graph[table]:
            in_degree[dependent_table] -= 1
            if in_degree[dependent_table] == 0:
                queue.append(dependent_table)

    if len(sorted_tables) != len(in_degree):
        raise ValueError(
            "Ciclo detectado nas dependências das tabelas. Não é possível realizar a ordenação topológica.")

    return sorted_tables


def get_primary_key(connection, table_name):
    """
    Retorna as colunas que fazem parte da chave primária (PRIMARY KEY) de uma tabela.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar as chaves primárias.

    Returns:
        list: Lista de colunas que fazem parte da chave primária.
    """
    query = """
    SELECT kcu.column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY';
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    primary_keys = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return primary_keys


def get_column_types(connection, table_name):
    """
    Retorna os tipos de dados das colunas de uma tabela.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar os tipos de dados.

    Returns:
        dict: Um dicionário onde as chaves são os nomes das colunas e os valores são os tipos de dados e metadados.
    """
    query = """
    SELECT 
        column_name, 
        data_type, 
        character_maximum_length, 
        numeric_precision, 
        numeric_scale
    FROM information_schema.columns
    WHERE table_name = %s;
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    
    column_types = []
    for row in cursor.fetchall():
        column_name = row[0]
        data_type = row[1]
        char_length = row[2]
        num_precision = row[3]
        num_scale = row[4]
        
        # Adicionar os detalhes do tipo
        lof = []
        if data_type == 'character varying' and char_length is not None:
            column_types.append([column_name, data_type, char_length])
        elif data_type == 'numeric' and num_precision is not None and num_scale is not None:
            column_types.append([column_name, data_type, num_precision, num_scale])
        else:
            column_types.append([column_name, data_type,])
        
    cursor.close()
    return column_types



def get_indexes(connection, table_name):
    """
    Retorna os índices associados a uma tabela e as colunas que eles cobrem.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar os índices.

    Returns:
        list: Lista de dicionários contendo o nome do índice e as colunas que ele cobre.
    """
    query = """
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename = %s;
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    indexes = [{"index_name": row[0], "definition": row[1]} for row in cursor.fetchall()]
    cursor.close()
    return indexes


def get_not_null_columns(connection, table_name):
    """
    Retorna as colunas que possuem a restrição NOT NULL.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar as colunas NOT NULL.

    Returns:
        list: Lista com os nomes das colunas que possuem a restrição NOT NULL.
    """
    query = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = %s AND is_nullable = 'NO';
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    not_null_columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return not_null_columns


def get_default_values(connection, table_name):
    """
    Retorna os valores padrão (DEFAULT) definidos para as colunas de uma tabela.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar os valores padrão.

    Returns:
        dict: Um dicionário onde a chave é o nome da coluna e o valor é o valor padrão.
    """
    query = """
    SELECT column_name, column_default
    FROM information_schema.columns
    WHERE table_name = %s AND column_default IS NOT NULL;
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    defaults = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    return defaults


def get_unique_constraints(connection, table_name):
    """
    Retorna as colunas com constraints de unicidade (UNIQUE CONSTRAINTS) de uma tabela.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar as constraints de unicidade.

    Returns:
        list: Lista de nomes de colunas que possuem a constraint UNIQUE.
    """
    query = """
    SELECT kcu.column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'UNIQUE' AND tc.table_name = %s;
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    unique_columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return unique_columns


def get_check_constraints(connection, table_name):
    """
    Retorna as constraints de verificação (CHECK CONSTRAINTS) associadas a uma tabela.

    Args:
        connection (psycopg2.connect): Conexão ativa com o banco de dados PostgreSQL.
        table_name (str): Nome da tabela para consultar as constraints.

    Returns:
        list: Lista de constraints e suas expressões de verificação.
    """
    query = """
    SELECT conname, consrc 
    FROM pg_constraint 
    JOIN pg_class ON conrelid = pg_class.oid 
    WHERE relname = %s AND contype = 'c';
    """
    cursor = connection.cursor()
    cursor.execute(query, (table_name,))
    constraints = [{"constraint_name": row[0], "check_expression": row[1]} for row in cursor.fetchall()]
    cursor.close()
    return constraints

def get_connection(host, dbname, port, user, password):
    return psycopg2.connect(host=host, dbname=dbname, port=port, user=user, password=password)


if __name__ == "__main__":
    try:
        connection = psycopg2.connect(host='localhost', dbname='mydatabase', port=5432, user='admin', password='admin')
        all_tables = get_all_tables(connection)
        print("Todas as tabelas:", all_tables)
        table_preview = get_table_data_preview(connection, "employee")
        print("Visualização dos dados da tabela 'employee':", table_preview)
        table_connections = get_table_connections(connection, "employee")
        print("Conexões da tabela 'employee':", table_connections)
    finally:
        if connection:
            connection.close()
