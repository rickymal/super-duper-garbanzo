import random
from datetime import datetime, timedelta
from typing import Callable, List, Tuple, Any

# 1. Criando a exceção personalizada
class ValidationError(Exception):
    """Exceção personalizada para erros de validação."""
    def __init__(self, message="Erro de validação ocorreu"):
        self.message = message
        super().__init__(self.message)


class ObjectValidator:
    def __init__(self, validator: Callable, generator: Callable):
        self.validator = validator
        self.generator = generator

    def validate(self, data_value: Any, klass, key) -> None:
        """Valida os dados com base no validador."""
        self.validator(data_value, klass, key)

    def generate(self) -> Any:
        """Gera dados aleatórios com base no gerador."""
        return self.generator()


import random



def decimal(min_value: float = 0.0, max_value: float = float('inf')) -> ObjectValidator:
    """Retorna um ObjectValidator para números decimais."""
    import decimal as dcm

    def validate(data: Any, klass: Any, key: str) -> None:
        if not isinstance(data, dcm.Decimal):  # Aceita int também pois é subclasse de float
            raise ValidationError(
                f"esperado número decimal, recebido: {type(data)}. "
                f"Recebido: {data} da classe {klass}, campo {key}"
            )

        # Convertemos para float para garantir comparação correta
        value = float(data)

        if not (min_value <= value <= max_value):
            raise ValidationError(
                f"Valor deve ser um decimal entre {min_value} e {max_value}. "
                f"Recebido: {data} da classe {klass}, campo {key}"
            )

    def generate():
        if max_value == float('inf'):
            # Se não há limite superior, geramos um número entre min_value e min_value + 1000
            upper_bound = min_value + 1000.0
        else:
            upper_bound = max_value

        # Gera um número decimal com até 4 casas decimais
        return round(random.uniform(min_value, upper_bound), 4)

    return ObjectValidator(validate, generate)

# Função para criar validadores de inteiros
def integer(min_value: int = 0, max_value: float = float('inf')) -> ObjectValidator:
    """Retorna um ObjectValidator para inteiros."""

    def validate(data: Any, klass: Any, key: str) -> None:
        if not isinstance(data, int):
            raise ValidationError(
                f"esperado inteiro, recebido: {type(data)}"
                f"Recebido: {data} da classe {klass}, campo {key}"
            )

        if min_value <= data <= max_value:
            raise ValidationError(
                f"Valor deve ser um inteiro entre {min_value} e {max_value}. "
                f"Recebido: {data} da classe {klass}, campo {key}"
            )

    def generate() -> int:
        if max_value == float('inf'):
            # Gera um número aleatório entre min_value e um valor grande (por exemplo, 10^6)
            return random.randint(min_value, 10**6)
        return random.randint(min_value, max_value)

    return ObjectValidator(validate, generate)

def string(min_length: int = 0, max_length: int = float('inf')) -> ObjectValidator:
    """Retorna um ObjectValidator para strings."""

    def validate(data: Any, klass, key) -> None:
        if not isinstance(data, str):
            raise ValidationError(f"erro na classe {klass}, campo {key}. Valor recebido do tipo {type(data)}, esperado string")

        if not (isinstance(data, str) and min_length <= len(data) <= max_length):
            raise ValidationError(f"erro na classe {klass}, campo {key}. String deve ter entre {min_length} e {max_length} caracteres. recebido {data}")

    def generate() -> str:
        length = random.randint(min_length, max_length)
        return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(length))

    return ObjectValidator(validate, generate)


from datetime import datetime, timedelta, timezone
import random
from typing import Any, Optional
from dateutil import parser
from dateutil import parser  # Importe a biblioteca dateutil
# Função para criar validadores de datas
def datetime_validator(
    min_date: Optional[Any] = None,
    max_date: Optional[Any] = None
) -> ObjectValidator:
    """Retorna um ObjectValidator para datas."""

    def validate(data: Any, klass: Any, key: str) -> None:
        # Função para converter strings ou objetos datetime
        def parse_date(value: Any) -> Optional[datetime]:
            if isinstance(value, str):
                try:
                    return parser.isoparse(value)
                except ValueError as err:
                    raise ValidationError(f"Formato de data inválido: {value}. Erro: {err}")
            elif isinstance(value, datetime):
                return value
            elif value is None:
                return None
            else:
                raise ValidationError(f"Tipo inválido para data: {type(value)}")

        # Converte min_date, max_date e data para datetime
        min_date_parsed = parse_date(min_date)
        max_date_parsed = parse_date(max_date)
        data_parsed = parse_date(data)

        # Verifica se todos os valores têm o mesmo tipo de timezone
        def get_timezone_type(date: Optional[datetime]) -> str:
            if date is None:
                return "none"
            return "naive" if date.tzinfo is None else "aware"

        timezone_types = {
            "min_date": get_timezone_type(min_date_parsed),
            "max_date": get_timezone_type(max_date_parsed),
            "data": get_timezone_type(data_parsed),
        }

        # Se houver valores com timezone misturados, lança um erro
        if len(set(timezone_types.values())) > 1:
            # Se min_date e max_date são None, ignora a validação de timezone
            if not (min_date_parsed is None and max_date_parsed is None):
                raise ValidationError(
                    f"Timezone misturados. min_date: {timezone_types['min_date']}, "
                    f"max_date: {timezone_types['max_date']}, data: {timezone_types['data']}"
                )

        # Se min_date e max_date são None, não há necessidade de ajustar o timezone
        if min_date_parsed is None and max_date_parsed is None:
            pass
        else:
            # Se nenhum valor tiver timezone, converte todos para UTC
            if all(tz == "naive" for tz in timezone_types.values()):
                if min_date_parsed is not None:
                    min_date_parsed = min_date_parsed.replace(tzinfo=timezone.utc)
                if max_date_parsed is not None:
                    max_date_parsed = max_date_parsed.replace(tzinfo=timezone.utc)
                if data_parsed is not None:
                    data_parsed = data_parsed.replace(tzinfo=timezone.utc)

        # Valida se o objeto é do tipo datetime e está dentro do intervalo
        if not isinstance(data_parsed, datetime):
            raise ValidationError(f"Valor deve ser um objeto datetime. Recebido: {data_parsed}")

        if min_date_parsed is not None and data_parsed < min_date_parsed:
            raise ValidationError(
                f"Data deve ser maior ou igual a {min_date_parsed}. "
                f"Recebido: {data_parsed} da classe {klass}, campo {key}"
            )

        if max_date_parsed is not None and data_parsed > max_date_parsed:
            raise ValidationError(
                f"Data deve ser menor ou igual a {max_date_parsed}. "
                f"Recebido: {data_parsed} da classe {klass}, campo {key}"
            )

    def generate() -> datetime:
        # Gera uma data aleatória entre min_date e max_date
        min_date_parsed = min_date if isinstance(min_date, datetime) else datetime(1900, 1, 1, tzinfo=timezone.utc)
        max_date_parsed = max_date if isinstance(max_date, datetime) else datetime.now(timezone.utc)

        delta = max_date_parsed - min_date_parsed
        random_days = random.randint(0, delta.days)
        return min_date_parsed + timedelta(days=random_days)

    return ObjectValidator(validate, generate)


def boolean() -> ObjectValidator:
    """Retorna um ObjectValidator para booleanos."""

    def validate(data: Any, klass, key) -> None:
        if not isinstance(data, bool):
            raise ValidationError("Valor deve ser um booleano.")

    def generate() -> bool:
        return random.choice([True, False])

    return ObjectValidator(validate, generate)

from dataclasses import dataclass

@dataclass
class DataObject:
    pass


def validate(klass: any, data_dict : dict, rich):
    expression = vars(klass)
    for key, val in data_dict.items():
        function = expression.get(key, None)
        if function is not None:
            function.validate(val, klass, key)
            rich.log("yellow", f"{key} validating ")
            continue
        rich.log("yellow", f"key {key} not found to be validated")



import pickle
import os
from typing import Any, List

def save_storage(key: str, value: Any) -> None:
    """
    Salva um valor em um arquivo de armazenamento usando pickle.
    Se o arquivo não existir, ele será criado.

    :param key: Nome do arquivo de armazenamento.
    :param value: Valor a ser adicionado ao armazenamento.
    """
    # Verifica se o arquivo já existe
    if os.path.exists(key):
        # Carrega os dados existentes
        with open(key, 'rb') as file:
            data: List[Any] = pickle.load(file)
    else:
        # Cria uma nova lista se o arquivo não existir
        data: List[Any] = []

    # Adiciona o novo valor à lista
    data.append(value)

    # Salva a lista atualizada no arquivo
    with open(key, 'wb') as file:
        pickle.dump(data, file)

    print(f"Valor salvo com sucesso no arquivo '{key}'.")


class Example(DataObject):
    name = string(min_length=0, max_length=999)



import random
from typing import Dict, List

# Recebe um dicionário e seleciona de forma randômica uma lista de chaves
def select_sample_keys(data: Dict, samples: int) -> List[str]:
    """Seleciona uma quantidade específica de chaves de forma aleatória."""
    keys = list(data.keys())
    if samples > len(keys):
        raise ValueError("O número de amostras não pode ser maior que o número de chaves.")
    return random.sample(keys, samples)


# Remove campos específicos de um dicionário
def remove_fields(data: Dict, fields: List[str]) -> Dict:
    """Remove as chaves especificadas do dicionário."""
    return {k: v for k, v in data.items() if k not in fields}


# Substitui os valores de campos específicos por zero-values
def zero_value_fields(data: Dict, fields: List[str]) -> Dict:
    """Substitui os valores das chaves especificadas por zero-values."""
    result = data.copy()
    for field in fields:
        if field in result:
            if isinstance(result[field], int) or isinstance(result[field], float):
                result[field] = 0
            elif isinstance(result[field], str):
                result[field] = ""
            elif isinstance(result[field], list):
                result[field] = []
            elif isinstance(result[field], dict):
                result[field] = {}
    return result


# Substitui os valores de campos específicos por None
def none_value_fields(data: Dict, fields: List[str]) -> Dict:
    """Substitui os valores das chaves especificadas por None."""
    result = data.copy()
    for field in fields:
        if field in result:
            result[field] = None
    return result


# Extrai apenas chaves específicas de um dicionário
def select_field(data: Dict, fields: List[str]) -> Dict:
    """Retorna um novo dicionário apenas com as chaves especificadas."""
    return {k: data[k] for k in fields if k in data}


# Combina dois dicionários, sobrescrevendo as chaves de `data` com as de `new_dict`
def merge_dict(data: Dict, new_dict: Dict) -> Dict:
    """Combina dois dicionários, sobrescrevendo as chaves de `data` com as de `new_dict`."""
    result = data.copy()
    result.update(new_dict)
    return result

