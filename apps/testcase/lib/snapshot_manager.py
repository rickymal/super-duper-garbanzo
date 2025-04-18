import datetime


class SnapshotManager:
    def __init__(self, name, schema_manager, max_store: int):
        self.name = name
        self.schema_manager = schema_manager
        self.max_store = max_store
        self.snapshots = []
        self.file = None

        from functools import partial, partialmethod
        

    @classmethod
    def create(cls):
        cls.__new__(cls)
        return cls

    def create_sub_snapshot(self, snaphot: str):
        new_snapshot = SnapshotManager.create()
        new_snapshot.name = snaphot
        new_snapshot.backward = self
        new_snapshot.forward = None
        new_snapshot.max_store = self.max_store
        new_snapshot.schema_builder = self.schema_builder
        new_snapshot.validator = self.validator
        new_snapshot.serializer = self.serializer
        new_snapshot.backward = self
        pass


    def calculate_hash(self, obj):
        """Calcula o hash do objeto para garantir a integridade."""
        return hashlib.sha256(pickle.dumps(obj)).hexdigest()
    
    def take_snapshot(self, data: any, description: str, **metadata):
        if self.max_store >= len(self.snapshots):
            self.snapshots.append((data, description, metadata))
            return 
        
        raise Exception("exceto de fotos tirada")

    def save_album(self):
        # Verificar se a pasta exist 

        snapshots_final = []
        
        schema = self.schema_manager.generate(self.snapshots)
        self.schema_manager.save(schema)


    def assert_value(self, data, mode: str, by: str):
        # Tenta carregar o reality_data (se não existir, salva data como referência)
        if not self.schema_manager.serializer.has_file():
            try:
                reality_data = self.schema_manager.serializer.load()
            except FileNotFoundError:
                self.take_snapshot(data=data, description='')
                self.save_album()
                reality_data = {'data': data}
        
        # Verificação completa (modo 'total')
        if mode == 'total':
            return self.schema_manager.validate_all_values(data)
        # Verificação parcial (modo 'partial')
        elif mode == 'partial':
            return self.schema_manager.validate_partial_values(data, reference = by)
        else:
            raise Exception("Formato 'mode' inválido")

    def assert_partial(self, data, by, reference):
        if by == 'input':
                # Verifica se cada item de `data` está presente e correto em `reference`
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in reference and reference[key] != value:
                        raise AssertionError(f"Valor incorreto para '{key}': esperado '{reference[key]}', mas encontrado '{value}'")
            elif isinstance(data, list):
                    # Compara cada item da lista `data` com os itens de `reference` (assumindo uma verificação parcial de correspondência)
                for item in data:
                    if item not in reference:
                        raise AssertionError(f"Item '{item}' não encontrado na referência.")
            else:
                    # Para dados primitivos, verifica igualdade direta com `reference`
                if data != reference:
                    raise AssertionError(f"Valor incorreto: esperado '{reference}', mas encontrado '{data}'")

        elif by == 'snapshot':
                # Verifica se cada item de `reference` está presente e correto em `data`
            if isinstance(reference, dict):
                for key, value in reference.items():
                    if key in data and data[key] != value:
                        raise AssertionError(f"Valor incorreto para '{key}': esperado '{value}', mas encontrado '{data.get(key)}'")
            elif isinstance(reference, list):
                    # Verifica se todos os itens de `reference` estão em `data`
                for item in reference:
                    if item not in data:
                        raise AssertionError(f"Item '{item}' da referência não encontrado no dado.")
            else:
                    # Para dados primitivos, verifica igualdade direta com `data`
                if reference != data:
                    raise AssertionError(f"Valor incorreto: esperado '{reference}', mas encontrado '{data}'")
        else:
            raise Exception("Formato 'by' inválido")

    def assert_total(self, data, reference):
        if type(data) != type(reference):
            raise AssertionError(f"Tipo incorreto: esperado '{type(reference).__name__}', mas encontrado '{type(data).__name__}'")

        if isinstance(data, dict):
                # Verificação exata para dicionários
            if data != reference:
                raise AssertionError("Estrutura e valores não correspondem no modo 'total'.")
            
        elif isinstance(data, list):
                # Verificação exata para listas
            if len(data) != len(reference) or any(item != ref for item, ref in zip(data, reference)):
                raise AssertionError("Listas não correspondem no modo 'total'.")
            
        else:
                # Verificação para dados primitivos
            if data != reference:
                raise AssertionError(f"Valor incorreto: esperado '{reference}', mas encontrado '{data}'")


    def assert_type(self, data):
        # Tenta carregar o reality_data (se não existir, salva data como referência)
        if not self.schema_manager.serializer.has_file():
            try:
                reality_data = self.schema_manager.serializer.load()
            except FileNotFoundError:
                self.schema_manager.take_snapshot(data=data, description='')
                self.schema_manager.save_album()
                reality_data = {'data': data}

        # Define o schema de referência para verificação de tipos
        reference = reality_data.get('schema', {})

        # Verifica se o schema contém as definições necessárias
        if 'properties' not in reference or 'required' not in reference:
            raise ValueError("O schema está incompleto ou malformado.")

        properties = reference['properties']
        required_fields = reference['required']

        # Verificação dos campos obrigatórios
        for required_field in required_fields:
            if required_field not in data:
                raise AssertionError(f"Campo obrigatório '{required_field}' ausente em 'data'.")
        isinstance()
        # Função auxiliar para verificar se o valor corresponde a pelo menos um dos tipos esperados
        def is_valid_type(value, expected_types):
            type_mapping = {
                'string': str,
                'integer': int,
                'number': float,
                'boolean': bool,
                'date': str  # Validado inicialmente como string
            }
            # Adiciona verificação específica para datas
            for expected_type in expected_types:
                if expected_type == 'date':
                    try:
                        datetime.datetime.strptime(value, "%Y-%m-%d")  # Exemplo de formato de data
                        return True
                    except (ValueError, TypeError):
                        continue
                elif isinstance(value, type_mapping.get(expected_type, object)):
                    return True
            return False

        # Verificação dos tipos para cada campo em 'data'
        for key, value in data.items():
            expected_types = properties.get(key, {}).get('type', [])
            if not expected_types:
                raise TypeError(f"O campo '{key}' não possui um tipo definido no schema.")

            # Checa se o valor está dentro dos tipos esperados
            if not is_valid_type(value, expected_types):
                expected_type_str = ', '.join(expected_types)
                raise TypeError(f"Tipo incorreto para '{key}': esperado {expected_type_str}, mas encontrado '{type(value).__name__}'")

     