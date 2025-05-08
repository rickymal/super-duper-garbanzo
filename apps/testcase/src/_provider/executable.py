import time
from abc import ABC, abstractmethod
from collections.abc import Callable

from data_object import ValidationError
from show_result import display_test_results


class IExecutable(ABC):

    @abstractmethod
    def run(self, output):
        pass


class Container(IExecutable):
    def __init__(self, name: str):
        self.futures = []
        self.name = name
        self.step_functions = []
        self.klass = []

    def it(self, klass):
        def decorator(step_func):
            if callable(step_func):  # Verifica se é chamável (função ou classe)
                self.add_step_klass(klass, step_func)  # Adiciona como classe
                return step_func  # Retorna para manter o funcionamento normal
            else:
                raise TypeError(f"Esperado uma função ou classe, mas recebeu {type(step_func)}.")
        return decorator

    def add_step_func(self, description, step_func: Callable):
        """Adiciona uma função como passo no pipeline."""
        self.step_functions.append((description, step_func))

    def add_step_klass(self, description, step_klass):

        from dataclasses import dataclass
        @dataclass
        class StepDefinitionKlass:
            description: str
            step: Callable

        """Adiciona uma classe como passo no pipeline."""
        self.klass.append(StepDefinitionKlass(description, step_klass))

    async def run(self, output):

        from dataclasses import dataclass
        @dataclass
        class StepDefinitionInstance:
            description: str
            step: Callable

        instances = [StepDefinitionInstance(k.description, k.step(output)) for k in self.klass]
        STEP_RESULT = []
        output.info(f"STEP_RESULT: {STEP_RESULT}")

        step_methods_name = ['before', 'step', 'after']
        for step_method_name in step_methods_name:
            for inst in instances:
                description = f"{inst.description} ({step_method_name})"
                reason = ""
                if hasattr(inst.step, step_method_name):
                    method = getattr(inst.step, step_method_name, None)
                    try:
                        if method:
                            method()
                            status = 2
                        else:
                            raise Exception(f"method {method} not found")
                    except ValidationError as err:
                        status = -1
                        output.write("red", f"d({inst.description}, {step_method_name}, ERROR): {err}")
                        reason = str(err)
                        STEP_RESULT.append((description, status, reason))
                        break

                    STEP_RESULT.append((description, status, reason))

        # output.info(STEP_RESULT)
        display_test_results(output.console, STEP_RESULT)