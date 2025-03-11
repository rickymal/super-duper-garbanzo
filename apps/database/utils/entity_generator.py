from dataclasses import dataclass, asdict

from jinja2 import Template
@dataclass
class TableName:
    snake: str
    camel: str

@dataclass
class Column:
    name: str
    python_type: str
    database_type: list[str]

@dataclass
class EntityGenerator:
    table_name: TableName
    columns: list[Column]
    deps: list[dict[str, str]]

    def render(self, template_path: str, output: str):
        with open(template_path, 'r', encoding='utf-8') as file:
            template = Template(file.read())
            obj = asdict(self)
            result = template.render(obj)

            with open(output, 'w', encoding='utf-8') as file:
                file.write(result)






import re

def to_snake_case(s: str) -> str:
    # Substitui as maiúsculas por _ seguido da versão minúscula
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    # Converte a string toda para minúscula
    return s.replace(" ", "_").lower()



def to_camel_case_capitalized(s: str) -> str:
    # Divide a string com base em não caracteres alfanuméricos, como espaços ou _
    words = re.split(r'[^a-zA-Z0-9]', s)
    # Capitaliza a primeira letra de cada palavra e junta
    return ''.join(word.capitalize() for word in words)


def to_camel_case(s: str) -> str:
    words = re.split(r'[^a-zA-Z0-9]', s)
    # Mantém a primeira palavra em minúscula e capitaliza as seguintes
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


# us = EntityGenerator(
#     table_name=TableName(snake = to_snake_case("employee_custom"), camel=to_camel_case("employee_custom")),
#     columns= [
#         Column(name = 'name', python_type='str', database_type=['varchar(30)', 'not_null()']),
#         Column(name = 'age', python_type='str', database_type=['varchar(30)', 'not_null()']),
#         Column(name = 'type', python_type='str', database_type=['varchar(30)', 'not_null()']),
#     ]
# )

# result = template.render(**asdict(us))

# with open(f'out.py', 'w', encoding='utf-8') as file:
#     file.write(result)
