import json

import output
from log import logger, RichStdOutputProtocol
import executable
import cmd
from broker import Broker

no_console = output.NoConsole()

def dynamic_function_name(prefix : str, postfix: list[any]):
    new_method_names = []
    for val in postfix:
        new_method_names.append(f"{prefix}{val}")

    return new_method_names

from datetime import time


tb = TestSuite(title = 'main')


services = tb.new_static(dynamic_function_name('step_', range(1, 11)))


# Todos os atores terão os metodos executados na hora em que foi declarada no static_dialog
@services.actor
class Actor:

    @services.description('fazer tarefa A')
    async def step_1(self):
        pass

    @services.description('fazer tarefa B')
    async def step_10(self):
        pass

@services.actor
class Actor:
    async def step_3(self):
        pass

    async def step_6(self):
        pass


from dataclasses import dataclass

@dataclasse
class ViewElement:
    name: str
    description: str
    type: str
    default_value: str | None


services = tb.new_timeline(dynamic_function_name('step_', range(1, 11)))

# irá intermediar um acesso ao banco de dados ou outro serviço por exemplo
# a ideia é permitir simular coisas como delay, timeout ou queda de conexão
# mas para isso preciso saber como eu vou 
@services.proxy('postgreSql database')
class Actor:
    
    async def init_application(self):
        if !cmd(["docker", "start", "idempiere-11"]):
            self.deny()

    async def close_service(self):
        bash(["docker", "pause", "idempiere-11"])
        