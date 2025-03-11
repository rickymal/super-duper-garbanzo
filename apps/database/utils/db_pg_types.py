from .meta import AbstractGenerator
from .meta import AbstractValidator
from enum import Enum,auto




class varchar(AbstractValidator):
    def __init__(self, size: int):
        self.size = size

    def validate(self, field):
        if field is None:
            return
        if len(field) > self.size:
            raise Exception("muito grande")

class number:
    pass

class email(AbstractGenerator):
    def generate(self) -> str:
        return "fakeemail@gmail.com"

class DatabaseType(Enum):
    NULL = auto()