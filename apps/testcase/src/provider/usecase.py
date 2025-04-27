import json

import output
from log import logger, RichStdOutputProtocol
import executable
import cmd
from broker import Broker

no_console = output.NoConsole()
sv = executable.Container(name = 'static service validation')

# prioridade infinita, significa que roda antes de tudo, quanto maior o número maior a prioridade
@sv.it('creating micro-services')
class Step: 
    def __init__(self):
        self.pid_payment = None
        self.pid_mdr = None
        self.pid_capture = None

    def before(self):
        self.pid_capture = cmd.run_script_and_get_pid('shell_cmds/init_capture.sh', RichStdOutputProtocol("capture"))
        self.pid_mdr = cmd.run_script_and_get_pid('shell_cmds/init_mdr.sh', RichStdOutputProtocol("mdr"))
        self.pid_payment = cmd.run_script_and_get_pid('shell_cmds/init_payment.sh', RichStdOutputProtocol("payment"))
        
    def after(self):
        logger.debug("killing process")
        cmd.kill_process(self.pid_capture.pid)
        cmd.kill_process(self.pid_mdr.pid)
        cmd.kill_process(self.pid_payment.pid)


@sv.it('initializing database')
class Step:
    def before(self):
        pass

    def after(self):
        pass


broker = Broker("brk", "rk","my_queue")

@sv.it('publicando informação no banco de dados')
def step():
    broker.publish(json.dumps({"oi" : "tutu pom"}))
    pass


@sv.it('publicando informação no banco de dados')
def step():
    broker.publish(json.dumps({"oi" : "tutu pom"}))
    pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import asyncio

class RichConsole:
    def __init__(self):
        self.console = Console()
        self.tests = {}  # Armazena os testes e seus status

    def get_table(self):
        table = Table(expand=True)
        table.add_column("Teste", style="bold cyan", no_wrap=True)
        table.add_column("Status", style="bold magenta")
        for test, status in self.tests.items():
            table.add_row(test, status)
        return table

    def update_display(self):
        # Limpa o terminal e reimprime a tabela encapsulada em um Panel
        self.console.clear()
        panel = Panel(self.get_table(), title="Resultados dos Testes", border_style="green")
        self.console.print(panel)

    async def on_run(self, container):
        self.console.log("[bold green]Iniciando a execução dos testes...[/bold green]")
        await asyncio.sleep(0)

    async def init_before_hook(self, container, hook):
        test_name = hook[0]
        self.console.log(f"[blue]Preparando: {test_name}[/blue]")
        self.tests[test_name] = "[yellow]Preparando[/yellow]"
        self.update_display()
        await asyncio.sleep(0)

    async def init_step(self, container, hook):
        test_name = hook[0]
        self.console.log(f"[cyan]Executando: {test_name}[/cyan]")
        self.tests[test_name] = "[yellow]Executando[/yellow]"
        self.update_display()
        await asyncio.sleep(0)

    async def init_after_hook(self, container, hook):
        test_name = hook[0]
        self.console.log(f"[blue]Concluindo: {test_name}[/blue]")
        # Caso não tenha sido definido anteriormente, marca como concluído
        self.tests[test_name] = self.tests.get(test_name, "[green]Concluído[/green]")
        self.update_display()
        await asyncio.sleep(0)

    async def on_success(self, container, hook):
        test_name = hook[0]
        self.console.log(f"[green]Sucesso: {test_name}[/green]")
        self.tests[test_name] = "[green]Sucesso[/green]"
        self.update_display()
        await asyncio.sleep(0)

    async def on_fail(self, container, hook, error):
        test_name = hook[0]
        self.console.log(f"[red]Falha: {test_name} | Erro: {error}[/red]")
        self.tests[test_name] = f"[red]Falha: {error}[/red]"
        self.update_display()
        await asyncio.sleep(0)

    async def on_finish(self, container):
        self.console.log("[bold red]Execução dos testes finalizada.[/bold red]")
        await asyncio.sleep(0)

# Exemplo de uso:
#
# async def main():
#     rich_console = RichConsole()
#     await rich_console.on_run(container=None)
#     await rich_console.init_before_hook(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.init_step(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.on_success(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.init_before_hook(None, ("Teste de logout",))
#     await asyncio.sleep(1)
#     await rich_console.init_step(None, ("Teste de logout",))
#     await asyncio.sleep(1)
#     await rich_console.on_fail(None, ("Teste de logout",), "Timeout na resposta")
#     await asyncio.sleep(1)
#     await rich_console.on_finish(None)
#
# asyncio.run(main())

# Exemplo de uso (para testes isolados):
#
# async def main():
#     rich_console = RichConsole()
#     await rich_console.on_run(container=None)
#     await rich_console.init_before_hook(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.init_step(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.on_success(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.init_before_hook(None, ("Teste de logout",))
#     await asyncio.sleep(1)
#     await rich_console.init_step(None, ("Teste de logout",))
#     await asyncio.sleep(1)
#     await rich_console.on_fail(None, ("Teste de logout",), "Timeout na resposta")
#     await asyncio.sleep(1)
#     await rich_console.on_finish(None)
#
# asyncio.run(main())

# Exemplo de como utilizar:
# async def main():
#     rich_console = RichConsole()
#     await rich_console.on_run(container=None)
#     await rich_console.init_before_hook(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.init_step(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     await rich_console.on_success(None, ("Teste de login",))
#     await asyncio.sleep(1)
#     rich_console.stop()
#
# asyncio.run(main())







class NoConsole:
    async def on_run(self, container):
        logger.debug("init")

    async def init_before_hook(self, container, hook):
        logger.info(hook[0])
        pass

    async def init_step(self, container, hook):
        logger.info(hook[0])
        pass

    async def init_after_hook(self, container, hook):
        logger.info(hook[0])
        pass

    async def on_success(self, container, hook):
        logger.info(hook[0])
        pass

    async def on_fail(self, container, hook, error):
        logger.info(hook[0])
        pass


asyncio.run(sv.run(output = RichConsole()))