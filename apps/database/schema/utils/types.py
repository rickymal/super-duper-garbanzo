from .base import abstract
from functools import lru_cache

class IntegerColumn(abstract.AbstractValidator):
    def __init__(self,):
        pass

    def validate(self, field):
        return


@lru_cache
def integer():
    return IntegerColumn()

class ReferenceColumn:
    def __init__(self, col):
        self.col = col
        pass


@lru_cache
def ref(col):
    return ReferenceColumn(col)


class TimestampWithoutTimeZone(abstract.AbstractValidator):
    def __init__(self):
        pass

    def validate(self, field):
        pass


@lru_cache
def timestampWithoutTimeZone():
    return TimestampWithoutTimeZone()



class VarcharColumn(abstract.AbstractValidator):
    def __init__(self, size: int):
        self.size = size

    def validate(self, field):
        if field is None:
            return
        if len(field) > self.size:
            raise Exception("muito grande")



@lru_cache
def varchar(size: int):
    return VarcharColumn(size)
