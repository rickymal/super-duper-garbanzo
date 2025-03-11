from functools import lru_cache

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