from abc import ABC, abstractmethod
from functools import lru_cache

class AbstractGenerator(ABC):

    @abstractmethod
    def generate(self) -> str:
        pass

class AbstractValidator(ABC):

    @abstractmethod
    def validate(self, column_name: str):
        pass