
from abc import ABC, abstractmethod

from .context import SchemaContext


class SerialType(ABC):

    @abstractmethod
    def acceptable_field_type(self) -> tuple:
        pass

    @abstractmethod
    def validate(self, field: SchemaContext):
        pass

    @abstractmethod
    def schema_format(self) -> str:
        pass




from datetime import datetime

def is_valid_date(date_string, date_format="%Y-%m-%d"):
    """
    Verifica se uma string é uma data válida.

    :param date_string: A string a ser validada.
    :param date_format: O formato da data (padrão: "%Y-%m-%d").
    :return: True se a string for uma data válida, False caso contrário.
    """
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False

class DateBaseFormat(SerialType):

    def acceptable_field_type(self):
        return str,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, str) and is_valid_date(ctx.field):
            ctx.approve()
        else:
            ctx.reject("tipo inválido")
            
    def schema_format(self):
        return {'type' : "date"}

class ArrayValidator(SerialType):

    def acceptable_field_type(self):
        return list,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, list):
            ctx.approve()
        else:
            ctx.reject()

    def schema_format(self):
        return {'type' : 'list'}


class StringValidator(SerialType):

    def acceptable_field_type(self):
        return str,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, str):
            ctx.approve()
        else:
            ctx.reject()

    def schema_format(self):
        return {'type' : 'text'}


class NumberValidator(SerialType):

    def acceptable_field_type(self):
        return float,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, float):
            ctx.approve()
        else:
            ctx.reject()

    def schema_format(self):
        return {'type' : 'number'}


class GenericObjectValidator(SerialType):

    def acceptable_field_type(self):
        return dict,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, dict):
            ctx.approve()
        else:
            ctx.reject()

    def schema_format(self):
        return {'type' : 'object'}



class IntegerValidator(SerialType):

    def acceptable_field_type(self):
        return int,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, int):
            ctx.approve()
        else:
            ctx.reject()

    def schema_format(self):
        return {'type' : 'integer'}

class BooleanValidator(SerialType):

    def acceptable_field_type(self):
        return bool,

    def validate(self, ctx: SchemaContext):
        if isinstance(ctx.field, bool):
            ctx.approve()
        else:
            ctx.reject()

    def schema_format(self):
        return {'type' : 'boolean'}


