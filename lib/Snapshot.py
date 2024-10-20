from abc import ABC, abstractmethod
import os
import hashlib
import time
import pickle
import json
import yaml
import toml
import hcl2
import re
import datetime
import logging

# Configurar o logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Interfaces e Implementações de Serializers ---

class SerializerInterface(ABC):
    @abstractmethod
    def save(self, data, file_path):
        pass

    @abstractmethod
    def load(self, file_path):
        pass


class JsonSerializer(SerializerInterface):
    def save(self, data, file_path):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def load(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)


class YamlSerializer(SerializerInterface):
    def save(self, data, file_path):
        with open(file_path, 'w') as f:
            yaml.dump(data, f)

    def load(self, file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)


class TomlSerializer(SerializerInterface):
    def save(self, data, file_path):
        with open(file_path, 'w') as f:
            toml.dump(data, f)

    def load(self, file_path):
        with open(file_path, 'r') as f:
            return toml.load(f)


class HclSerializer(SerializerInterface):
    def save(self, data, file_path):
        hcl_str = self.dict_to_hcl(data)
        with open(file_path, 'w') as f:
            f.write(hcl_str)

    def load(self, file_path):
        with open(file_path, 'r') as f:
            return hcl2.load(f)

    def dict_to_hcl(self, d, indent=0):
        hcl_str = ''
        for key, value in d.items():
            hcl_str += '  ' * indent + f'{key} = {self.format_hcl_value(value, indent)}\n'
        return hcl_str

    def format_hcl_value(self, value, indent):
        if isinstance(value, dict):
            return '{\n' + self.dict_to_hcl(value, indent + 1) + '  ' * indent + '}'
        elif isinstance(value, list):
            return '[{}]'.format(', '.join([self.format_hcl_value(v, indent) for v in value]))
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif value is None:
            return 'null'
        else:
            raise TypeError(f'Unsupported type: {type(value)}')


class PickleSerializer(SerializerInterface):
    def save(self, data, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)

    def load(self, file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)

# --- Context e Validator Interface ---

class Context:
    """Contexto passado para as funções de validação."""
    def __init__(self, data, schema, path):
        self.data = data          # Dados atuais sendo validados
        self.schema = schema      # Esquema correspondente
        self.path = path          # Caminho até o dado atual
        self.errors = []          # Lista de erros de validação

    def approve(self):
        """Marca a validação como aprovada."""
        pass  # Nada a fazer; a aprovação é implícita se nenhum erro for adicionado

    def reprove(self, message):
        """Adiciona uma mensagem de erro."""
        self.errors.append({'path': self.path, 'message': message})


class ValidatorInterface(ABC):
    @abstractmethod
    def validate(self, ctx, engine):
        pass

# --- Implementação dos Validadores ---

class ObjectValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        # Validação de propriedades
        properties = schema.get('properties', {})
        for key, subschema in properties.items():
            subdata = data.get(key)
            subpath = f"{ctx.path}.{key}"
            subctx = Context(subdata, subschema, subpath)
            is_valid, errors = engine.validate(subdata, subschema)
            ctx.errors.extend(errors)

        # Validação de regras adicionais
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")


class ArrayValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        items_schema = schema.get('items', {})
        for index, item in enumerate(data):
            subpath = f"{ctx.path}[{index}]"
            subctx = Context(item, items_schema, subpath)
            is_valid, errors = engine.validate(item, items_schema)
            ctx.errors.extend(errors)

        # Validação de regras adicionais, se houver
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")


class StringValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        # Validações específicas para strings
        min_length = schema.get('minLength')
        max_length = schema.get('maxLength')
        pattern = schema.get('pattern')

        if min_length is not None and len(data) < min_length:
            ctx.reprove(f"Comprimento da string é menor que o mínimo de {min_length} em {ctx.path}")

        if max_length is not None and len(data) > max_length:
            ctx.reprove(f"Comprimento da string é maior que o máximo de {max_length} em {ctx.path}")

        if pattern is not None:
            if not re.match(pattern, data):
                ctx.reprove(f"A string '{data}' não corresponde ao padrão regex '{pattern}' em {ctx.path}")

        # Validações adicionais
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")


class IntegerValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        # Validações específicas para inteiros
        minimum = schema.get('minimum')
        maximum = schema.get('maximum')

        if minimum is not None and data < minimum:
            ctx.reprove(f"Valor {data} é menor que o mínimo de {minimum} em {ctx.path}")

        if maximum is not None and data > maximum:
            ctx.reprove(f"Valor {data} é maior que o máximo de {maximum} em {ctx.path}")

        # Validações adicionais
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")


class NumberValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        # Validações específicas para números
        minimum = schema.get('minimum')
        maximum = schema.get('maximum')
        multiple_of = schema.get('multipleOf')

        if minimum is not None and data < minimum:
            ctx.reprove(f"Valor {data} é menor que o mínimo de {minimum} em {ctx.path}")

        if maximum is not None and data > maximum:
            ctx.reprove(f"Valor {data} é maior que o máximo de {maximum} em {ctx.path}")

        if multiple_of is not None and (data % multiple_of != 0):
            ctx.reprove(f"Valor {data} não é múltiplo de {multiple_of} em {ctx.path}")

        # Validações adicionais
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")


class BooleanValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        # Validações adicionais, se houver
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")


class NullValidator(ValidatorInterface):
    def validate(self, ctx, engine):
        data = ctx.data
        schema = ctx.schema

        if data is not None:
            ctx.reprove(f"Esperado valor nulo, mas encontrado {type(data).__name__} em {ctx.path}")

        # Validações adicionais, se houver
        validations = schema.get('validations', {})
        for logic_op, rules in validations.items():
            if logic_op in ['and', 'or']:
                results = [engine._apply_validation_rule(ctx, rule) for rule in rules]
                if logic_op == 'and' and not all(results):
                    ctx.reprove(f"Falha nas validações 'and' em {ctx.path}")
                elif logic_op == 'or' and not any(results):
                    ctx.reprove(f"Falha nas validações 'or' em {ctx.path}")
            else:
                res = engine._apply_validation_rule(ctx, rules)
                if not res:
                    ctx.reprove(f"Falha na validação em {ctx.path}")

# --- ValidatorFactory ---

class ValidatorFactory:

    def __init__(self):
        self.validators = {}


    def register_validator(self, type_name, validator_class):
        self.validators[type_name] = validator_class

    def get_validator(self, type_name):
        validator_class = self.validators.get(type_name)
        if not validator_class:
            raise ValueError(f"Tipo de validação '{type_name}' não suportado.")
        return validator_class()

# --- ValidationRule e ValidationEngine ---

class ValidationRule:
    def __init__(self, name, function):
        self.name = name
        self.function = function

    def apply(self, context):
        return self.function(context)


class ValidationEngine:
    def __init__(self, validator_factory: ValidatorFactory):
        self.rules = {}
        self.validator_factory = validator_factory

    def register_rule(self, name, function):
        """Registra uma função de validação personalizada."""
        self.rules[name] = ValidationRule(name, function)

    def validate(self, data, schema):
        """Valida os dados com base no esquema."""
        context = Context(data, schema, 'root')
        self._validate(context)
        is_valid = len(context.errors) == 0
        return is_valid, context.errors

    def _validate(self, ctx):
        """Função recursiva para validar os dados."""
        validator = self.validator_factory.get_validator(ctx.schema.get('type'))
        validator.validate(ctx, self)

    def _apply_validation_rule(self, ctx, rule):
        """Aplica uma regra de validação."""
        if 'pythonFunctionNameRegister' in rule:
            func_name = rule['pythonFunctionNameRegister']
            func = self.rules.get(func_name)
            if not func:
                ctx.reprove(f"Função de validação '{func_name}' não registrada")
                return False
            # Executa a função de validação
            func.apply(ctx)
            if ctx.errors:
                return False
            return True
        elif 'and' in rule or 'or' in rule:
            # Trata validações aninhadas
            logic_op = 'and' if 'and' in rule else 'or'
            rules = rule[logic_op]
            results = [self._apply_validation_rule(ctx, subrule) for subrule in rules]
            if logic_op == 'and':
                return all(results)
            else:
                return any(results)
        else:
            ctx.reprove(f"Regra de validação inválida em {ctx.path}")
            return False

# --- Funções de Validação Personalizadas ---

def schema_only(ctx: Context):
    """Validação básica apenas pelo esquema."""
    pass  # A validação básica já foi realizada

def regexOption(ctx: Context):
    """Valida se a string corresponde à regex fornecida."""
    pattern = getattr(ctx, 'args', None)
    if pattern is None:
        ctx.reprove("Padrão regex não fornecido.")
        return
    if not re.match(pattern, ctx.data):
        ctx.reprove(f"O valor '{ctx.data}' não corresponde ao padrão regex '{pattern}'")

def validateDataLogic(ctx: Context):
    """Valida se a data 'end' é posterior à data 'start'."""
    date_keys = getattr(ctx, 'date_key_names', None)
    date_format = getattr(ctx, 'date_format', '%Y-%m-%d')
    
    if not date_keys or len(date_keys) != 2:
        ctx.reprove("Nomes das chaves de data não fornecidos ou insuficientes.")
        return
    
    start_date_str = ctx.data.get(date_keys[0])
    end_date_str = ctx.data.get(date_keys[1])
    
    if not start_date_str or not end_date_str:
        ctx.reprove("Datas de início ou fim ausentes.")
        return
    
    try:
        start_date = datetime.strptime(start_date_str, date_format)
        end_date = datetime.strptime(end_date_str, date_format)
        if end_date <= start_date:
            ctx.reprove(f"A data '{end_date_str}' não é posterior à data '{start_date_str}'")
    except Exception as e:
        ctx.reprove(f"Erro ao converter datas: {e}")

# --- SerializerFactory ---

class SerializerFactory:
    def __init__(self):
        self.serializers = {}

    def register_serializer(self, format_name, serializer_class):
        self.serializers[format_name] = serializer_class

    def get_serializer(self, format_name):
        serializer_class = self.serializers.get(format_name)
        if not serializer_class:
            raise ValueError(f"Formato '{format_name}' não suportado.")
        return serializer_class()

# --- SchemaGeneratorInterface e DefaultSchemaGenerator ---

class SchemaGeneratorInterface(ABC):
    @abstractmethod
    def generate(self, data):
        pass


class DefaultSchemaGenerator(SchemaGeneratorInterface):
    def generate(self, obj):
        """Gera um esquema de tipos a partir do objeto fornecido."""
        if isinstance(obj, dict):
            schema = {'type': 'object', 'properties': {}, 'required': []}
            for key, value in obj.items():
                schema['properties'][key] = self.generate(value)
                schema['required'].append(key)  # Por padrão, todos os campos são obrigatórios
            return schema
        elif isinstance(obj, list):
            if obj:
                # Assume que todos os itens da lista são do mesmo tipo
                schema = {'type': 'array', 'items': self.generate(obj[0])}
            else:
                schema = {'type': 'array', 'items': {}}
            return schema
        elif isinstance(obj, str):
            return {'type': 'string'}
        elif isinstance(obj, int):
            return {'type': 'integer'}
        elif isinstance(obj, float):
            return {'type': 'number'}
        elif isinstance(obj, bool):
            return {'type': 'boolean'}
        elif obj is None:
            return {'type': 'null'}
        else:
            raise TypeError(f'Unsupported type: {type(obj)}')

# --- Snapshot Class com Métodos de Asserção ---

class SnapshotManager:
    def __init__(self, snapshot_name, serializer=None, validation_mode='hard', snapshot_dir='mock', schema_generator=None, validation_engine=None):
        self.snapshot_name = snapshot_name
        self.validation_mode = validation_mode
        self.snapshot_dir = snapshot_dir
        self.schema_generator = schema_generator or DefaultSchemaGenerator()
        self.validation_engine = validation_engine or ValidationEngine()
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        self.serializer = serializer  # Pode ser None

    def set_serializer(self, serializer):
        self.serializer = serializer

    def select_serializer(self, format):
        """Seleciona o serializer com base no formato."""
        serializers = {
            'json': JsonSerializer(),
            'yml': YamlSerializer(),
            'yaml': YamlSerializer(),
            'toml': TomlSerializer(),
            'hcl': HclSerializer(),
            'pkl': PickleSerializer(),
            'pickle': PickleSerializer()
        }
        serializer = serializers.get(format)
        if not serializer:
            raise ValueError(f"Formato '{format}' não suportado.")
        return serializer

    def addRegister(self, name, func):
        """Registra uma função de validação personalizada."""
        self.validation_engine.register_rule(name, func)

    def calculate_hash(self, obj):
        """Calcula o hash do objeto para garantir a integridade."""
        return hashlib.sha256(pickle.dumps(obj)).hexdigest()

    def create_snapshot(self, obj, version='latest', metadata=None, format='pkl'):
        """Cria um novo snapshot."""
        serializer = self.serializer or self.select_serializer(format)
        self.validation_engine.register_rule('custom_validation', validateDataLogic)  # Exemplo de registro
        current_time = time.time()
        versioned_file = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version}.{format}')
        schema = self.schema_generator.generate(obj)
        snapshot_data = {
            'schema': schema,
            'snapshot': obj,
            'hash': self.calculate_hash(obj),
            'version': version,
            'created_at': datetime.datetime.fromtimestamp(current_time).isoformat() if not isinstance(serializer, PickleSerializer) else current_time,
            'last_access': datetime.datetime.fromtimestamp(current_time).isoformat() if not isinstance(serializer, PickleSerializer) else current_time,
            'metadata': metadata or {}
        }
        serializer.save(snapshot_data, versioned_file)
        logger.info(f"Snapshot criado em {versioned_file} com metadados: {metadata}")
        return obj

    def get_or_create_snapshot(self, obj=None, version='latest', expiration_time=3600, format='pkl'):
        """Obtém ou cria um snapshot."""
        serializer = self.serializer or self.select_serializer(format)
        versioned_file = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version}.{format}')
        current_time = time.time()

        if os.path.exists(versioned_file):
            snapshot_data = serializer.load(versioned_file)
            # Converter timestamps se necessário
            if not isinstance(serializer, PickleSerializer):
                if isinstance(snapshot_data['created_at'], str):
                    snapshot_data['created_at'] = datetime.datetime.fromisoformat(snapshot_data['created_at']).timestamp()
                if isinstance(snapshot_data['last_access'], str):
                    snapshot_data['last_access'] = datetime.datetime.fromisoformat(snapshot_data['last_access']).timestamp()
            # Verifica expiração
            if current_time - snapshot_data['created_at'] > expiration_time:
                logger.info(f"Snapshot {version} expirou. Criando um novo.")
                if obj is not None:
                    return self.create_snapshot(obj, version, format=format)
                else:
                    raise ValueError(f"Snapshot {version} expirou e nenhum objeto foi fornecido para criar um novo.")
            # Validação do hash
            if self.calculate_hash(snapshot_data['snapshot']) != snapshot_data['hash']:
                raise ValueError(f"Snapshot {version} está corrompido!")
            # Validação dos dados
            is_valid, errors = self.validate_data(snapshot_data['snapshot'], snapshot_data['schema'])
            if not is_valid:
                error_messages = '\n'.join([f"{e['path']}: {e['message']}" for e in errors])
                if self.validation_mode == 'hard':
                    raise ValueError(f"Erro de validação ao carregar o snapshot:\n{error_messages}")
                else:
                    logger.warning(f"Advertência de validação ao carregar o snapshot:\n{error_messages}")
            # Atualiza o tempo de último acesso
            snapshot_data['last_access'] = datetime.datetime.fromtimestamp(current_time).isoformat() if not isinstance(serializer, PickleSerializer) else current_time
            # Salva o snapshot atualizado
            serializer.save(snapshot_data, versioned_file)
            logger.info(f"Recuperando snapshot de {versioned_file}")
            return snapshot_data['snapshot']
        else:
            if obj is not None:
                return self.create_snapshot(obj, version, metadata=None, format=format)
            else:
                raise FileNotFoundError(f"Snapshot {version} não encontrado e nenhum objeto foi fornecido para criar um novo.")

    def load_snapshot_data(self, version='latest', format='pkl'):
        """Carrega os dados do snapshot sem realizar validações."""
        serializer = self.serializer or self.select_serializer(format)
        versioned_file = os.path.join(self.snapshot_dir, f'{self.snapshot_name}_{version}.{format}')

        if os.path.exists(versioned_file):
            snapshot_data = serializer.load(versioned_file)
            # Converter timestamps se necessário
            if not isinstance(serializer, PickleSerializer):
                if isinstance(snapshot_data['created_at'], str):
                    snapshot_data['created_at'] = datetime.datetime.fromisoformat(snapshot_data['created_at']).timestamp()
                if isinstance(snapshot_data['last_access'], str):
                    snapshot_data['last_access'] = datetime.datetime.fromisoformat(snapshot_data['last_access']).timestamp()
            return snapshot_data
        else:
            raise FileNotFoundError(f"Snapshot {version} não encontrado.")

    def validate_data(self, data, schema, path='root'):
        """Valida os dados com base no esquema e nas validações personalizadas."""
        return self.validation_engine.validate(data, schema)

    # Métodos de asserção adicionados
    def assert_deep_equal(self, data, version='latest', format='pkl'):
        """Asserta que os dados fornecidos são profundamente iguais ao snapshot salvo."""
        snapshot_data = self.load_snapshot_data(version, format)
        snapshot_content = snapshot_data['snapshot']

        if snapshot_content != data:
            raise AssertionError(f"Os dados fornecidos não são iguais ao snapshot '{version}'.")
        else:
            logger.info(f"Asserção bem-sucedida: os dados são iguais ao snapshot '{version}'.")

    def assert_schema_compliance(self, data, version='latest', format='pkl'):
        """Asserta que os dados fornecidos estão em conformidade com o esquema do snapshot."""
        snapshot_data = self.load_snapshot_data(version, format)
        schema = snapshot_data['schema']
        is_valid, errors = self.validate_data(data, schema)
        if not is_valid:
            error_messages = '\n'.join([f"{e['path']}: {e['message']}" for e in errors])
            raise AssertionError(f"Os dados não estão em conformidade com o esquema:\n{error_messages}")
        else:
            logger.info(f"Asserção bem-sucedida: os dados estão em conformidade com o esquema do snapshot '{version}'.")

    def assert_custom_validation(self, data, version='latest', format='pkl'):
        """Asserta que os dados fornecidos passam nas validações personalizadas."""
        snapshot_data = self.load_snapshot_data(version, format)
        schema = snapshot_data['schema']
        is_valid, errors = self.validate_data(data, schema)
        if not is_valid:
            error_messages = '\n'.join([f"{e['path']}: {e['message']}" for e in errors])
            raise AssertionError(f"Os dados não passaram nas validações personalizadas:\n{error_messages}")
        else:
            logger.info(f"Asserção bem-sucedida: os dados passaram nas validações personalizadas do snapshot '{version}'.")

# --- Exemplo de Uso Completo ---

if __name__ == '__main__':
    # Instancia a classe Root com seus componentes

    # Exemplo de objeto com campos adicionais
    my_data = {
        "lightDataVerification": {
            "start": "2024-05-03",
            "end": "2024-05-05"
        },
        "softDataVerification": {
            "start": "2024-05-03",
            "end": "2024-05-05"
        },
        "hardDataVerification": {
            "start": "2024-05-03",
            "end": "2024-05-05"
        },
        "status": True,
        "count": 10,
        "price": 99.99,
        "description": "Produto de teste",
        "notes": None
    }

    # Definindo serializadores
    serializerFactory = SerializerFactory()
    serializerFactory.register_serializer('json', JsonSerializer)
    serializerFactory.register_serializer('yaml', YamlSerializer)
    serializerFactory.register_serializer('toml', TomlSerializer)
    serializerFactory.register_serializer('hcl', HclSerializer)
    serializerFactory.register_serializer('pickle', PickleSerializer)

    # Definindo validador
    validatorFactory = ValidatorFactory()
    validatorEngine = ValidationEngine(validatorFactory)
    validatorFactory.register_validator('object', ObjectValidator)
    validatorFactory.register_validator('array', ArrayValidator)
    validatorFactory.register_validator('string', StringValidator)
    validatorFactory.register_validator('integer', IntegerValidator)
    validatorFactory.register_validator('number', NumberValidator)
    validatorFactory.register_validator('boolean', BooleanValidator)
    validatorFactory.register_validator('null', NullValidator)
    validatorEngine.register_rule('schema-only', schema_only)
    validatorEngine.register_rule('regex', regexOption)
    validatorEngine.register_rule('validateDataLogic', validateDataLogic)


    default_schema_generator = DefaultSchemaGenerator()

    # Atualizar o esquema no objeto de dados
    # Para incluir as validações, precisamos embutir 'validations' no esquema armazenado no snapshot
    # Portanto, o método create_snapshot deve receber o esquema com as validações
    # Ajustar o método create_snapshot para aceitar um esquema personalizado (se necessário)

    # Criar snapshot com esquema que inclui validações
    snapshot_json = SnapshotManager(
        snapshot_name='my_test_snapshot_json',
        serializer=serializerFactory,
        schema_generator=default_schema_generator,
        validation_engine=validatorEngine
    )
    snapshot_json.create_snapshot(my_data, version='0.0.1', metadata={"author": "Henrique"})

    # Criar snapshot em formato HCL
    snapshot_hcl = SnapshotManager(
        snapshot_name='my_test_snapshot_hcl',
        serializer=serializerFactory,
        schema_generator=default_schema_generator,
        validation_engine=validatorEngine
    )
    snapshot_hcl.create_snapshot(my_data, version='0.0.1', metadata={"author": "Henrique"})

    # Exemplo de uso do assert_deep_equal
    try:
        snapshot_json.assert_deep_equal(my_data, version='0.0.1')
        print("assert_deep_equal passou com sucesso para snapshot_json.")
    except AssertionError as e:
        print(f"AssertionError: {e}")

    # Modificando os dados para causar uma falha na asserção
    altered_data = {
        "lightDataVerification": {
            "start": "2024-05-03",
            "end": "2024-05-06"  # Alterado para uma data diferente
        },
        "softDataVerification": {
            "start": "2024-05-03",
            "end": "2024-05-05"
        },
        "hardDataVerification": {
            "start": "2024-05-03",
            "end": "2024-05-05"
        },
        "status": False,  # Alterado
        "count": 5,        # Alterado
        "price": 49.99,    # Alterado
        "description": "Produto alterado",  # Alterado
        "notes": "Nota adicional"  # Alterado de None para string
    }

    # Tentando a asserção com dados alterados
    try:
        snapshot_json.assert_deep_equal(altered_data, version='0.0.1')
        print("assert_deep_equal passou com sucesso para os dados alterados.")
    except AssertionError as e:
        print(f"AssertionError: {e}")

    # Exemplo de uso do assert_schema_compliance
    try:
        snapshot_json.assert_schema_compliance(altered_data, version='0.0.1')
        print("assert_schema_compliance passou com sucesso para os dados alterados.")
    except AssertionError as e:
        print(f"AssertionError: {e}")

    # Exemplo de uso do assert_custom_validation
    try:
        snapshot_json.assert_custom_validation(altered_data, version='0.0.1')
        print("assert_custom_validation passou com sucesso para os dados alterados.")
    except AssertionError as e:
        print(f"AssertionError: {e}")
