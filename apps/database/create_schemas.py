from utils import map_pg
from utils import db_pg_types
from utils import entity_generator
import pdb 
from collections import defaultdict
conn = map_pg.get_connection('localhost', 'mydatabase', 5432, 'admin', 'admin')

def to_postgresql_format(col_options, val):
    val_ = defaultdict(list)
    for key, vals in val.items():
        for val in vals:
            val_[val[0]].append(f"ref({entity_generator.to_camel_case_capitalized(key)}Entity.{val[1]})")


    for col in col_options:


        if col[1] == 'integer':
            yield entity_generator.Column(name = col[0], python_type='int', database_type=[
                f"{entity_generator.to_camel_case(col[1])}()",
                *val_.get(col[0], []),
            ])
        elif col[1] == 'timestamp without time zone':
            yield entity_generator.Column(name = col[0], python_type='str', database_type=[
                f"{entity_generator.to_camel_case(col[1])}()",
                *val_.get(col[0], []),
            ])
        elif col[1] == 'character varying':
            yield entity_generator.Column(name = col[0], python_type='str', database_type=[
                f"varchar({col[2]})",
                *val_.get(col[0], []),
            ])
        elif col[1] == 'text':
            yield entity_generator.Column(name = col[0], python_type='str', database_type=[
                f"text()",
                *val_.get(col[0], []),
            ])
        elif col[1] == 'numeric':
            yield entity_generator.Column(name = col[0], python_type='int', database_type=[
                f"numeric({col[2]}, {col[3]})",
                *val_.get(col[0], []),
            ])
        else:
            pdb.set_trace()

    return 


dependencies = map_pg.get_table_dependencies(connection=conn)
all_tables = map_pg.get_all_tables(connection=conn)

import os
for table_name in all_tables:
    col_options = map_pg.get_column_types(connection=conn, table_name=table_name)

    deps = dependencies.get(table_name, {})
    eg = entity_generator.EntityGenerator(
        table_name=entity_generator.TableName(
            snake = entity_generator.to_snake_case(table_name), 
            camel = entity_generator.to_camel_case_capitalized(table_name),
        ),
        columns=[col for col in to_postgresql_format(col_options, deps)],
        deps=[{'snake': f"{entity_generator.to_snake_case(dep)}_entity", 'camel': f"{entity_generator.to_camel_case_capitalized(dep)}Entity" } for dep in deps.keys()]
    )

    eg.render(os.path.join('templates', 'py_entity_creation.jinja'), os.path.join('schema', f"{entity_generator.to_snake_case(table_name)}_entity.py"))


