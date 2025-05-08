
# Classe BaseOutput (para gerenciamento de saída)
from abc import ABC, abstractmethod


class BaseOutput(ABC):
    @abstractmethod
    def start_test_instance(self, test_instance):
        pass

    @abstractmethod
    def end_test_instance(self, test_instance):
        pass

    @abstractmethod
    def start_container(self, container):
        pass

    @abstractmethod
    def end_container(self, container):
        pass

    @abstractmethod
    def start_pipeline(self, pipeline):
        pass

    @abstractmethod
    def end_pipeline(self, pipeline, status):
        pass

    @abstractmethod
    def start_step(self, step):
        pass

    @abstractmethod
    def end_step(self, step, status):
        pass

    @abstractmethod
    def log(self, message: str):
        pass




# Classe BaseOutput (para gerenciamento de saída)
class NoConsole(BaseOutput):
    
    def start_test_instance(self, test_instance):
        pass

    
    def end_test_instance(self, test_instance):
        pass

    
    def start_container(self, container):
        pass

    
    def end_container(self, container):
        pass

    
    def start_pipeline(self, pipeline):
        pass

    
    def end_pipeline(self, pipeline, status):
        pass

    
    def start_step(self, step):
        pass

    
    def end_step(self, step, status):
        pass

    
    def log(self, message: str):
        print(message)
        pass




from rich.console import Console
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Classe RichConsole que herda de BaseOutput
class RichConsole(BaseOutput):
    def __init__(self):
        self.console = Console()
        self.test_tree = None
        self.current_nodes = []
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        )
        self.tasks = {}
        self.progress_started = False

    def start_test_instance(self, test_instance):
        self.test_tree = Tree(f"[bold cyan]{test_instance.name}[/bold cyan]")
        self.current_nodes.append(self.test_tree)
        if not self.progress_started:
            self.progress_started = True
            self.progress.__enter__()

    def end_test_instance(self, test_instance):
        if self.progress_started:
            self.progress.__exit__(None, None, None)
        self.console.print(self.test_tree)
        self.current_nodes.pop()

    def start_container(self, container):
        node = self.current_nodes[-1].add(f"[bold]{container.name}[/bold]")
        self.current_nodes.append(node)

    def end_container(self, container):
        self.current_nodes.pop()

    def start_pipeline(self, pipeline):
        node = self.current_nodes[-1].add(f"[yellow]{pipeline.name}[/yellow]")
        self.current_nodes.append(node)
        task_id = self.progress.add_task(f"Executando Pipeline: {pipeline.name}", total=None)
        self.tasks[pipeline] = task_id

    def end_pipeline(self, pipeline, status):
        task_id = self.tasks.pop(pipeline, None)
        if task_id is not None:
            self.progress.remove_task(task_id)
        status_text = "[green]SUCESSO[/green]" if status == "PASSED" else "[red]FALHA[/red]"
        self.current_nodes[-1].label = f"[yellow]{pipeline.name}[/yellow] - {status_text}"
        self.current_nodes.pop()

    def start_step(self, step):
        node = self.current_nodes[-1].add(f"{step.description}")
        self.current_nodes.append(node)
        task_id = self.progress.add_task(f"Executando Step: {step.description}", total=None)
        self.tasks[step] = task_id

    def end_step(self, step, status):
        task_id = self.tasks.pop(step, None)
        if task_id is not None:
            self.progress.remove_task(task_id)
        status_text = "[green]SUCESSO[/green]" if status == "PASSED" else "[red]FALHA[/red]"
        self.current_nodes[-1].label = f"{step.description} - {status_text}"
        self.current_nodes.pop()

    def log(self, message: str):
        # Loga a mensagem no console atual
        self.console.log(message)
