import os 
import asyncio
from library import migrator


pg_source = {
    "dbname": "sourcedb",
    "user": "admin",
    "password": "admin",
    "host": "localhost",
    "port": 5433
}

pg_dest = {
    "dbname": "destdb",
    "user": "admin",
    "password": "admin",
    "host": "localhost",
    "port": 5434
}

tables = ["usuarios", "pagamentos"]

asyncio.run(
    migrator.migrate_postgres_tables_async(
        pg_source, pg_dest,
        tables=tables,
        batch_size=1000,
        truncate_before=True
    )
)
