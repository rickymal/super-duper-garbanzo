
from abc import ABC, abstractmethod
from functools import lru_cache

class AbstractValidator(ABC):

    @abstractmethod
    def validate(self, column_name: str):
        pass

class AbstractGenerator(ABC):

    @abstractmethod
    def generate(self) -> str:
        pass

class ColumnMeta(type):
    def __new__(cls, name, bases, dct, providers=None):
        dct['validators'] = [prov for prov in providers if hasattr(prov, 'validate')]
        dct['generators'] = [prov for prov in providers if hasattr(prov, 'generate')]
        return super().__new__(cls, name, bases, dct)


@lru_cache()
def column(*providers) -> type:
    class Column(metaclass=ColumnMeta, providers = providers):
        pass
    return Column

class VarcharColumn(AbstractValidator):
    def __init__(self, size: int):
        self.size = size

    def validate(self, field):
        if field is None:
            return
        if len(field) > self.size:
            raise Exception("muito grande")



