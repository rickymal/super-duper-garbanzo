from jinja2 import Template



from dataclasses import dataclass

@dataclass
class UpdateStmt:
    table_name: str
    table_col_name: list[str]
    table_col_value: list[str]


class Connection:
    conn: any
    templates: dict[str, Template]

    def __init__(self):
        self.conn = psycopg2.connect(host='localhost', dbname='mydatabase', port=5432, user='admin', password='admin')
        self.templates = {}
        for action in ['create', 'read', 'update', 'delete']:
            with open(f'crud/postgresql/{action}.jinja', 'r', encoding='utf-8') as file:
                self.templates[action] = Template(file.read())

    def execute(self, action: str, stmt):
        query = self.templates[action].render(**asdict(stmt))
        with open("output.sql", 'w', encoding='utf-8') as file:
            file.write(query)
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()

    def create(self, stmt: UpdateStmt):
        self.execute('create', stmt)



class DefaultConnectionEntity:

    def __init__(self, conn: Connection):
        self.conn = conn
        self.providers = self._build_providers()

    def _build_providers(self) -> dict:
        """Cria um cache de provedores (columns) para reutilizar."""
        providers = {key: val() for key, val in self.__annotations__.items()}
        return providers



    def _generate_values(self, inspector: dict) -> dict:
        values = {}

        for param, value in inspector.items():
            # Gera valores padrão
            if value is None:
                for gen in self.providers[param].generators:
                    value = gen.generate()
                    if value is not None:
                        break

            # Valida os valores
            for val in self.providers[param].validators:
                val.validate(value)

            if value is None:
                continue

            if (val := self.py2sql(value)) is not None:
                values[param] = val
        return values

    def py2sql(self, val: any):
        if val == True:
            return "true"

        if val == False:
            return "false"

        if val == DatabaseType.NULL:
            return "null"

        if isinstance(val, str):
            return f"'{val}'"
        return val
    def create(self, **columns):
        inspector = inspect.currentframe().f_locals
        params = tuple(inspector.keys())[1:]
        values = self._generate_values({param: inspector[param] for param in params})

        stmt = UpdateStmt(
            table_name=self.table_name(),
            table_col_name=list(values.keys()),
            table_col_value=[list(values.values())]
        )

        self.conn.create(stmt)
