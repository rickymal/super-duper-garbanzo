from abc import ABC, abstractmethod
from collections.abc import Callable

class IExecutable(ABC):

    @abstractmethod
    def run(self, output):
        pass


class Container(IExecutable):
    def __init__(self, name: str):
        self.futures = []
        self.name = name
        self.step_functions = []
        self.step_klasses = []

    def it(self, description):
        def decorator(step_func):
            if callable(step_func):  # Verifica se é chamável (função ou classe)
                if isinstance(step_func, type):  # Verifica se é uma classe
                    # Verifica se a classe tem os métodos obrigatórios
                    has_before = hasattr(step_func, "before") and callable(getattr(step_func, "before"))
                    has_after = hasattr(step_func, "after") and callable(getattr(step_func, "after"))
                    if not has_before or not has_after:
                        raise TypeError(f"A classe `{step_func.__name__}` deve implementar `before` e `after`.")
                    self.add_step_klass(description, step_func)  # Adiciona como classe
                else:
                    self.add_step_func(description, step_func)  # Adiciona como função
                return step_func  # Retorna para manter o funcionamento normal
            else:
                raise TypeError(f"Esperado uma função ou classe, mas recebeu {type(step_func)}.")
        return decorator

    def add_step_func(self, description, step_func: Callable):
        """Adiciona uma função como passo no pipeline."""
        self.step_functions.append((description, step_func))

    def add_step_klass(self, description, step_klass):
        """Adiciona uma classe como passo no pipeline."""
        self.step_klasses.append((description, step_klass))

    async def run(self, output):
        self.before_hooks = [val for val in self.step_klasses]
        self.after_hooks = [val for val in self.step_klasses]
        self.step_hooks = self.step_functions
        await output.on_run(self)
        import asyncio

        for bhook in self.before_hooks:
            await output.init_before_hook(self, bhook)
            try:
                bhook[1]().before()
                await output.on_success(self, bhook)
            except Exception as err:
                await output.on_fail(self, bhook, err)

        for bhook in self.step_hooks:
            await output.init_step(self, bhook)
            try:
                bhook[1]()
                await output.on_success(self, bhook)
            except Exception as err:
                await output.on_fail(self, bhook, err)

        for bhook in self.after_hooks:
            await output.init_after_hook(self, bhook)
            try:
                bhook[1]().after()
                await output.on_success(self, bhook)
            except Exception as err:
                await output.on_fail(self, bhook, err)