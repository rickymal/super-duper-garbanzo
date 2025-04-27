# testsuite.py
from __future__ import annotations
import time
import functools, inspect, textwrap, types, sys
from typing import Callable, Dict, List, Any
import pickle
import asyncio

# --- infra de saída simples (cores ANSI) -------------------------------
GREEN, CYAN, RESET = "\033[92m", "\033[96m", "\033[0m"
def log(msg: str, colour: str = CYAN):
    print(f"{colour}{msg}{RESET}")

# ----------------------------------------------------------------------
class _Step:
    """Representa 1 passo dentro de um Actor."""
    def __init__(self, fn: Callable, template: str):
        self.fn        = fn
        self.name      = fn.__name__
        self.template  = template           # p.ex. "open postgres docker {{url}}"

    def render(self, params: Dict[str, Any]) -> str:
        # converte {{var}} → {var} pra usar str.format
        fmt = self.template.replace("{{", "{").replace("}}", "}")
        try:
            return fmt.format(**params)
        except KeyError as e:
            missing = e.args[0]
            raise ValueError(f"Parâmetro obrigatório '{missing}' não informado em ts.run()")


from dataclasses import dataclass
import rich
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import re

@dataclass
class Step:
    descr: str
    method: Callable

from library import cmd

def interpolate_data(descr: str, data: dict) -> str:
    """Substitui {{var}} por data[var] em descr."""
    # converte {{var}} → {var} pra usar str.format
    pattern = r"\{\{(.*?)\}\}"
    matches = re.findall(pattern, descr)
    fmt = descr.replace("{{", "{").replace("}}", "}")

    data = {key: value for key, value in data.items() if key in matches}
    try:
        return fmt.format(**data), data
    except KeyError as e:
        missing = e.args[0]
        raise ValueError(f"Parâmetro obrigatório '{missing}' não informado em ts.run()")

def get_methods(descr: str) -> List[str]:
    """Extrai os nomes dos métodos a partir da descrição."""
    # converte {{var}} → {var} pra usar str.format
    fmt = descr.replace("{{", "{").replace("}}", "}")
    try:
        return [x.strip() for x in fmt.split(",")]
    except KeyError as e:
        missing = e.args[0]
        raise ValueError(f"Parâmetro obrigatório '{missing}' não informado em ts.run()")
    
def filter_args(arguments: Dict[str, Any], method_names: List[str]) -> Dict[str, Any]:
    """Filtra os argumentos, mantendo apenas os que estão na lista de métodos."""
    filtered_args = {}
    for method_name in method_names:
        if method_name in arguments:
            filtered_args[method_name] = arguments[method_name]
    return filtered_args
import cmd
# ----------------------------------------------------------------------
class _ActorMeta:
    def __init__(self, label: str):
        self.label  = label                 # "PostgreSQL Application"
        self.steps = []   # mapeia nome_do_método → _Step
        self.console = rich.get_console()

    def step(self, descr: str, method: Callable):
        self.steps.append(Step(descr, method))

    def __init__(self, label: str):
        self.label = label
        self.steps = []
        self.console = rich.get_console()
        self.execution_times = self._load_execution_times()

    def _load_execution_times(self) -> Dict[str, float]:
        """Load average execution times from pickle file"""
        try:
            with open('.execution_times.pkl', 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def _save_execution_time(self, method_name: str, execution_time: float):
        """Save execution time to pickle file"""
        times = self.execution_times
        if method_name not in times:
            times[method_name] = execution_time
        else:
            # Calculate running average
            times[method_name] = (times[method_name] + execution_time) / 2
        
        with open('.execution_times.pkl', 'wb') as f:
            pickle.dump(times, f)

    async def run_all(self, arguments):
        from library import cmd
        
        for step in self.steps:
            text, filtered_args = interpolate_data(step.descr, arguments)
            self.console.print(f"[bold cyan]{text}[/]")
            
            method_name = step.method.__name__
            self.console.print(f"Running {method_name}()...")
            
            start_time = time.time()
            try:
                if inspect.iscoroutinefunction(step.method):
                    executed_method = step.method(self, **filtered_args)
                    await executed_method
                else:
                    step.method(self, **filtered_args)
                    
            except cmd.FailTest as e:
                self.console.print(f"[red]Error in {method_name} {e.title}(): {e}[/]")
                for line in e.log_message.splitlines():
                    self.console.print(f"  [red]{line}[/]")
                raise

            execution_time = time.time() - start_time
            self._save_execution_time(method_name, execution_time)
            
            self.console.print(f"  [green]✓[/] {method_name}() completed in {execution_time:.2f}s")

def actor(description: str):
    """Decorator para registrar um actor."""
    return _ActorMeta(description)