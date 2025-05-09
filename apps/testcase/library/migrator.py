import asyncio
import pdb

import psycopg2
import psycopg2.extras
from rich.console import Console

async def migrate_postgres_tables_async(source_pg, destiny_pg, tables, batch_size=1000, truncate_before=False,
                                        exclude_columns=None, sql_pre_commit = None, sql_pos_commit = None):
    if exclude_columns is None:
      exclude_columns = []

    if sql_pre_commit is None:
        sql_pre_commit = []

    if sql_pos_commit is None:
        sql_pos_commit = []
    console = Console()

    if destiny_pg["host"] != "localhost":
        raise Exception("opa meu patrão, acho que você trocou os parâmetros ein?!")

    def connect(config):
        return psycopg2.connect(
            dbname=config["dbname"],
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config.get("port", 5432)
        )

    def table_exists(cursor, table_name):
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table_name,))
        return cursor.fetchone()[0]

    def copy_table_schema(src_cursor, dest_cursor, table):
        src_cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table,))
        columns = src_cursor.fetchall()
        if not columns:
            raise ValueError(f"Table '{table}' does not exist in source database")

        column_defs = []
        for col in columns:
            colname, datatype, nullable, char_len = col
            if datatype == "character varying" and char_len:
                datatype = f"VARCHAR({char_len})"
            elif datatype == "character":
                datatype = "CHAR"
            elif datatype == "integer":
                datatype = "INTEGER"
            elif datatype == "timestamp without time zone":
                datatype = "TIMESTAMP"

            null_clause = "" if nullable == "YES" else "NOT NULL"
            column_defs.append(f"{colname} {datatype} {null_clause}")

        create_stmt = f"CREATE TABLE {table} (\n  {', '.join(column_defs)}\n);"
        dest_cursor.execute(create_stmt)

    loop = asyncio.get_event_loop()

    with connect(source_pg) as src_conn, connect(destiny_pg) as dest_conn:
        src_cur = src_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        dest_cur = dest_conn.cursor()

        dest_cur.execute("SET session_replication_role = 'replica';")
        dest_conn.commit()

        for sql_stmt in sql_pre_commit:
            dest_cur.execute(sql_stmt)
            dest_conn.commit()


        for table in tables:
            if not table_exists(dest_cur, table):
                console.print(f"[blue]Tabela {table} não existe. Criando no banco de destino...[/blue]")
                copy_table_schema(src_cur, dest_cur, table)
                dest_conn.commit()

        if truncate_before:
            for table in tables:
                if table_exists(dest_cur, table):
                    console.print(f"[yellow]Truncating {table}...[/yellow]")
                    dest_cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
            dest_conn.commit()

        for table in tables:
            offset = 0
            total_copied = 0
            while True:
                src_cur.execute(f"SELECT * FROM {table} OFFSET %s LIMIT %s;", (offset, batch_size))


                rows = src_cur.fetchall()
                if not rows:
                    break

                # 1. identificar a posição de onde quero remover


                colnames = []
                idx_to_be_removed = []
                for idx, desc in enumerate(src_cur.description):
                    if desc[0] not in exclude_columns:
                        colnames.append(desc[0])
                        continue

                    idx_to_be_removed.append(idx)

                for row in rows:
                    for idx in idx_to_be_removed:
                        del row[idx]

                placeholders = ','.join(['%s'] * len(colnames))
                insert_query = f"INSERT INTO {table} ({', '.join(colnames)}) VALUES ({placeholders})"

                try:
                    await loop.run_in_executor(None, dest_cur.executemany, insert_query, rows)
                    await loop.run_in_executor(None, dest_conn.commit)
                except Exception as error:
                    query = dest_cur.mogrify(insert_query, row).decode('utf-8')
                    raise error

                offset += batch_size
                total_copied += len(rows)
                console.print(f"[blue]{table}[/blue] → Copied [green]{total_copied}[/green] rows...")

        for sql_stmt in sql_pos_commit:
            dest_cur.execute(sql_stmt)
            dest_conn.commit()

        dest_cur.execute("SET session_replication_role = 'origin';")
        dest_conn.commit()

    console.print("[bold green]Migration completed successfully![/bold green]")
