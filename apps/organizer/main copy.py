import os
import re
import yaml
import uuid
import pickle
from datetime import datetime
from rich.console import Console

console = Console()

DATA_FILE = 'tasks.pico'
CONFIG_FILE = 'config.yaml'


def build_scrum_queue(ctx: ApplicationContext):
    """
    Retorna uma lista de todas as tarefas 'folha' (cujos filhos estão finalizados ou inexistentes),
    que ainda não estão finalizadas, ordenadas por priority_score (crescente = maior prioridade).
    """
    all_tasks = ctx.task_manager.all_tasks()
    leaf_tasks = []
    for t in all_tasks:
        if not ctx.task_manager.is_leaf(t.id):
            continue
        if t.status != 'finalizado':
            leaf_tasks.append(t)
    # Ordenar pelo priority_score (menor score => maior prioridade).
    leaf_tasks_sorted = sorted(leaf_tasks, key=lambda x: x.priority_score)
    return leaf_tasks_sorted

def scrum_loop(ctx: ApplicationContext, mode: str):
    """
    Loop infinito que:
     - Monta a fila de tarefas-folha (não finalizadas)
     - Percorre cada tarefa, perguntando "o que foi feito?", "dificuldades?" e "o que vai fazer?"
     - Se 'o que vai fazer?' vier vazio, a tarefa é bloqueada
     - Se o usuário digitar '@exit', encerramos o loop
     - Ao chegar no fim da fila, voltamos ao início (round-robin)
     - Se todas ficarem bloqueadas ou finalizadas, saímos do loop
    Param 'mode': 'ask' ou 'daily', para registrar no histórico.
    """

    console.print(f"[bold underline]Entrando no loop do Scrum ({mode.upper()})[/bold underline]")

    while True:
        # Reconstrói a fila a cada “ciclo” (round-robin)
        queue = build_scrum_queue(ctx)

        # Se a fila estiver vazia => ou tudo finalizado, ou tudo bloqueado
        if not queue:
            console.print("[bold yellow]Nenhuma tarefa 'folha' disponível (tudo bloqueado ou finalizado). Saindo do loop.[/bold yellow]")
            break

        # Percorre todas as tarefas da fila
        for task in queue:
            # Se a qualquer momento o usuário digitar '@exit', vamos sair completamente
            # Vamos checar de forma simples: se ele digitar esse comando no prompt
            # (Veremos mais adiante no input).
            if task.status == 'finalizado' or task.blocked:
                continue  # pula, pois acabou de mudar ou algo assim

            console.print(f"\n[bold green]Tarefa em discussão: {task.id} - {task.description}[/bold green]")
            done = console.input("[cyan]O que você fez? (enter = nada) [/cyan]")
            blocking = console.input("[cyan]Dificuldades? (enter = nenhuma) [/cyan]")

            # Aqui faremos um 'input' que pode ser interpretado como '@exit' ou "vou fazer X"
            next_action = console.input("[cyan]O que vai fazer agora? (enter = nada -> block / '@exit' -> sair) [/cyan]")

            if next_action.strip().lower() == "@exit":
                console.print("[bold red]Saindo do loop de Scrum (por comando @exit).[/bold red]")
                return  # sai da função entire

            if not next_action.strip():
                # Se nada for digitado, consideramos bloqueio
                console.print("Nenhuma ação informada. Tarefa será marcada como bloqueada.", style="bold red")
                task.blocked = True
                task.block_reason = blocking if blocking else "Bloqueada sem motivo específico."
            else:
                # Se fez algo, mudar para 'iniciado' se estava pendente
                if task.status == 'pendente':
                    task.status = 'iniciado'

                # Salva no histórico
                task.history.append({
                    'timestamp': datetime.now(),
                    'mode': mode,  # só pra saber se foi 'ask' ou 'daily'
                    'done': done,
                    'blocking': blocking,
                    'todo': next_action
                })
                console.print("Informações salvas.", style="green")

            # Persistência
            ctx.task_manager.save()

        # Ao final desse “for” (rodamos todas as tarefas da fila), repetimos no while True.
        # Se ainda existirem tarefas não finalizadas/não bloqueadas, recomeçamos (round-robin).
        # Se nenhuma sobrar, o while True romperá no próximo ciclo.



class Task:
    def __init__(self, description: str):
        self.id = str(uuid.uuid4())[:8]
        self.description = description
        self.status = 'pendente'
        self.history = []
        self.blocked = False
        self.block_reason = None
        self.block_duration = None
        self.creation_time = datetime.now()
        self.priority_score = 4  # menor valor = maior prioridade

    def __str__(self):
        return (
            f"Task(ID={self.id}, Desc='{self.description}', "
            f"Status={self.status}, Blocked={self.blocked}, "
            f"Priority={self.priority_score})"
        )

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, task: Task):
        self.nodes[task.id] = task
        if task.id not in self.edges:
            self.edges[task.id] = set()

    def add_edge(self, parent_id: str, child_id: str):
        if parent_id not in self.edges:
            self.edges[parent_id] = set()
        self.edges[parent_id].add(child_id)

    def get_task_by_prefix(self, prefix: str):
        for t_id, task in self.nodes.items():
            if t_id.startswith(prefix):
                return task
        return None

    def get_children(self, task_id: str):
        children_ids = self.edges.get(task_id, set())
        return [self.nodes[cid] for cid in children_ids]

    def all_tasks(self):
        return list(self.nodes.values())

    def is_leaf(self, task_id: str):
        if task_id not in self.edges:
            return True
        children_ids = self.edges[task_id]
        if not children_ids:
            return True
        for cid in children_ids:
            child = self.nodes[cid]
            if child.status != 'finalizado':
                return False
        return True

class TaskManager:
    def __init__(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                saved_data = pickle.load(f)
                # Esperamos que saved_data seja um dicionário com {'graph': ...}
                self.graph = saved_data['graph']
        else:
            self.graph = Graph()

    def save(self):
        data = {
            'graph': self.graph
        }
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(data, f)

    def create_task(self, description: str):
        t = Task(description)
        self.graph.add_node(t)
        self.save()
        return t

    def link_tasks(self, parent_id: str, child_id: str):
        self.graph.add_edge(parent_id, child_id)
        self.save()

    def get_task_by_prefix(self, prefix: str):
        return self.graph.get_task_by_prefix(prefix)

    def all_tasks(self):
        return self.graph.all_tasks()

    def is_leaf(self, task_id: str):
        return self.graph.is_leaf(task_id)

    def get_children(self, task_id: str):
        return self.graph.get_children(task_id)

class ApplicationContext:
    def __init__(self, task_manager: TaskManager, config):
        self.task_manager = task_manager
        self.config = config
        self.selected_tasks = set()
        self.scrum_queue = []

class CommandInterpreter:
    def __init__(self, ctx: ApplicationContext):
        self.ctx = ctx
        self.commands = {}

    def register_method(self, name, func):
        self.commands[name] = func

    def parse_and_execute(self, line: str):
        raw_tokens = line.split('@')
        tokens = [t.strip() for t in raw_tokens if t.strip()]

        if not tokens:
            console.print("[bold red]Nenhum comando detectado.[/bold red]")
            return

        for t in tokens:
            parts = t.split(None, 1)
            if len(parts) == 1:
                cmd = parts[0]
                param = ""
            else:
                cmd, param = parts[0], parts[1]

            cmd = cmd.strip().lower()
            param = param.strip()

            if cmd in self.commands:
                self.commands[cmd](self.ctx, param)
            else:
                console.print(f"[bold red]Comando @{cmd} não reconhecido.[/bold red]")

# =========================== COMANDOS EXISTENTES ===========================

def add_task(ctx: ApplicationContext, param: str):
    if not param:
        console.print("Uso: @todo <descrição>", style="bold red")
        return
    t = ctx.task_manager.create_task(param)
    for sel_id in ctx.selected_tasks:
        ctx.task_manager.link_tasks(sel_id, t.id)
    console.print(f"Tarefa criada: {t.id} -> '{t.description}'", style="green")

def select_task(ctx: ApplicationContext, param: str):
    if not param:
        console.print("Uso: @select <prefix>", style="bold red")
        return
    task = ctx.task_manager.get_task_by_prefix(param)
    if task:
        ctx.selected_tasks.add(task.id)
        console.print(f"Tarefa {task.id} ('{task.description}') selecionada.", style="cyan")
    else:
        console.print(f"Nenhuma tarefa com prefixo '{param}'.", style="bold red")

def deselect_task(ctx: ApplicationContext, param: str):
    if not param:
        console.print("Uso: @deselect <prefix>", style="bold red")
        return
    task = ctx.task_manager.get_task_by_prefix(param)
    if task and task.id in ctx.selected_tasks:
        ctx.selected_tasks.remove(task.id)
        console.print(f"Tarefa {task.id} ('{task.description}') des-selecionada.", style="cyan")
    else:
        console.print(f"Tarefa não encontrada ou não estava selecionada: '{param}'", style="bold red")

def priority_cmd(ctx: ApplicationContext, param: str):
    if not param:
        console.print("Uso: @priority <prefix1> <prefix2> ...", style="bold red")
        return
    parts = param.split()
    if len(parts) < 2:
        console.print("Passe ao menos 2 prefixos para comparar.", style="bold red")
        return
    tasks = []
    for p in parts:
        t = ctx.task_manager.get_task_by_prefix(p)
        if t:
            tasks.append(t)
        else:
            console.print(f"[bold red]Nenhuma tarefa com prefixo '{p}'.[/bold red]")

    if len(tasks) < 2:
        console.print("[bold red]Poucas tarefas encontradas para comparar prioridades.[/bold red]")
        return

    # Bubble sort interativo
    n = len(tasks)
    for i in range(n):
        for j in range(i + 1, n):
            t1 = tasks[i]
            t2 = tasks[j]
            console.print(f"\nComparando: [cyan]{t1.id} ({t1.description})[/cyan] vs [magenta]{t2.id} ({t2.description})[/magenta]")
            console.print("Digite [bold green]yes[/bold green] se a primeira é mais importante, [bold red]no[/bold red] se a segunda é mais importante, ou [bold yellow]same[/bold yellow] se forem equivalentes.")
            ans = console.input("[yes/no/same]? ").strip().lower()
            if ans == 'no':
                tasks[i], tasks[j] = tasks[j], tasks[i]
            elif ans == 'same':
                pass
            else:
                pass

    base_score = 1
    for t in tasks:
        t.priority_score = base_score
        base_score *= 2
        console.print(f"Tarefa [cyan]{t.id}[/cyan] ('{t.description}') => Nova pontuação: {t.priority_score}")

    ctx.task_manager.save()
    console.print("[bold green]Prioridades atualizadas com sucesso![/bold green]")

def scrum_master(ctx: ApplicationContext, param: str):
    console.print("[bold underline]Scrum Master - Início[/bold underline]")
    ctx.scrum_queue.clear()
    all_tasks = ctx.task_manager.all_tasks()

    leaf_tasks = []
    for t in all_tasks:
        if not ctx.task_manager.is_leaf(t.id):
            continue
        if t.status != 'finalizado':
            leaf_tasks.append(t)

    leaf_tasks_sorted = sorted(leaf_tasks, key=lambda x: x.priority_score)
    ctx.scrum_queue = leaf_tasks_sorted

    if not ctx.scrum_queue:
        console.print("[bold red]Nenhuma tarefa 'folha' pendente para discutir.[/bold red]")
        return

    console.print(f"Tarefas-folha pendentes em fila: {len(ctx.scrum_queue)}", style="cyan")
    console.print("Use @ask, @block, @finish ou @daily para interagir.\n", style="dim")

def ask_about_task(ctx: ApplicationContext, param: str):
    """
    @ask
    Inicia loop infinito de perguntas sobre todas as tarefas-folha não finalizadas/bloqueadas,
    em round-robin, até digitar @exit ou tudo ficar bloqueado/finalizado.
    """
    scrum_loop(ctx, mode="ask")



def block_task(ctx: ApplicationContext, param: str):
    if not ctx.scrum_queue:
        console.print("Não há tarefas na fila de Scrum para bloquear. Use @scrum.", style="bold red")
        return
    task = ctx.scrum_queue[0]
    console.print(f"Tarefa {task.id} - {task.description} será bloqueada.")
    reason = console.input("Por que está bloqueada? ")
    duration = console.input("Quanto tempo de bloqueio? (ex: 1w 3d 4h 3m) ")
    task.blocked = True
    task.block_reason = reason if reason else "Bloqueada sem motivo."
    task.block_duration = duration if duration else "Indefinido"
    task.history.append({
        'timestamp': datetime.now(),
        'blocked': True,
        'block_reason': task.block_reason,
        'block_duration': task.block_duration
    })
    ctx.task_manager.save()
    console.print("Tarefa bloqueada com sucesso.", style="bold yellow")


def daily_log(ctx: ApplicationContext, param: str):
    """
    @daily
    Mesmo comportamento de 'ask', mas marcamos 'mode=daily' no histórico,
    se você quiser diferenciar. Mantemos a lógica de round-robin infinito.
    """
    scrum_loop(ctx, mode="daily")


def finish_task(ctx: ApplicationContext, param: str):
    if not ctx.scrum_queue:
        console.print("Não há tarefas na fila de Scrum para finalizar. Use @scrum.", style="bold red")
        return

    task = ctx.scrum_queue[0]
    task.status = 'finalizado'
    task.blocked = False
    console.print(f"Tarefa {task.id} ('{task.description}') marcada como finalizada.", style="bold green")
    task.history.append({
        'timestamp': datetime.now(),
        'finished': True,
    })
    ctx.task_manager.save()
    ctx.scrum_queue.pop(0)

    # Recalcular a fila
    new_leaf_tasks = []
    all_tasks = ctx.task_manager.all_tasks()
    for t in all_tasks:
        if not ctx.task_manager.is_leaf(t.id):
            continue
        if t.status != 'finalizado':
            new_leaf_tasks.append(t)
    new_leaf_tasks_sorted = sorted(new_leaf_tasks, key=lambda x: x.priority_score)
    ctx.scrum_queue = new_leaf_tasks_sorted
    console.print("Fila de Scrum atualizada.", style="dim")

# =========================== (RE)ADICIONANDO @list E @show ===========================

from rich.table import Table

# =========================== (RE)ADICIONANDO @list E @show ===========================

def list_tasks_cmd(ctx: ApplicationContext, param: str):
    """
    @list
    Lista apenas as tarefas em status pendente ou iniciado, ordenadas por prioridade.
    Exibe em tabela (usando rich).
    """
    tasks = ctx.task_manager.all_tasks()
    # Filtra só as não-finalizadas
    filtered = [t for t in tasks if t.status != 'finalizado']
    # Ordena por score (menor score => maior prioridade)
    filtered_sorted = sorted(filtered, key=lambda x: x.priority_score)

    if not filtered_sorted:
        console.print("[bold red]Não há tarefas ativas para listar.[/bold red]")
        return

    # Cria uma tabela Rich
    table = Table(title="Tarefas Ativas", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Descrição", style="bold")
    table.add_column("Status")
    table.add_column("Blocked", justify="center")
    table.add_column("Priority", justify="right")

    for t in filtered_sorted:
        table.add_row(
            t.id,
            t.description,
            t.status,
            str(t.blocked),
            str(t.priority_score)
        )

    console.print(table)


def show_tasks_cmd(ctx: ApplicationContext, param: str):
    """
    @show
    Mostra todas as tarefas, inclusive finalizadas, em tabela (Rich).
    """
    tasks = ctx.task_manager.all_tasks()
    # Ordenar por priority_score, apenas para consistência
    tasks_sorted = sorted(tasks, key=lambda x: x.priority_score)

    if not tasks_sorted:
        console.print("[bold red]Não há tarefas registradas.[/bold red]")
        return

    table = Table(title="Todas as Tarefas", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Descrição", style="bold")
    table.add_column("Status")
    table.add_column("Blocked", justify="center")
    table.add_column("Priority", justify="right")

    for t in tasks_sorted:
        table.add_row(
            t.id,
            t.description,
            t.status,
            str(t.blocked),
            str(t.priority_score)
        )

    console.print(table)


# ============================== FUNÇÃO PRINCIPAL ===============================
def main():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    tm = TaskManager()
    ctx = ApplicationContext(tm, config)
    interpreter = CommandInterpreter(ctx)

    # REGISTRANDO TODOS OS COMANDOS, INCLUINDO list E show
    interpreter.register_method("todo", add_task)
    interpreter.register_method("select", select_task)
    interpreter.register_method("deselect", deselect_task)
    interpreter.register_method("priority", priority_cmd)
    interpreter.register_method("scrum", scrum_master)
    interpreter.register_method("ask", ask_about_task)
    interpreter.register_method("block", block_task)
    interpreter.register_method("daily", daily_log)
    interpreter.register_method("finish", finish_task)

    # OS DOIS COMANDOS REINSERIDOS:
    interpreter.register_method("list", list_tasks_cmd)
    interpreter.register_method("show", show_tasks_cmd)

    console.print("[bold magenta]Bem-vindo ao CLI de Gerenciamento de Tarefas (versão Grafos + Prioridade)![/bold magenta]\n")
    console.print("Comandos disponíveis:\n"
                 "  @todo <descricao>\n"
                 "  @select <prefix>\n"
                 "  @deselect <prefix>\n"
                 "  @priority <prefix1> <prefix2> ...\n"
                 "  @scrum\n"
                 "  @ask\n"
                 "  @block\n"
                 "  @daily\n"
                 "  @finish\n"
                 "  @list\n"
                 "  @show\n", style="dim")

    while True:
        try:
            line = console.input("> ")
            if '@' not in line:
                console.print("Nenhum '@' encontrado. Use o formato correto (ex: @todo 'Minha tarefa').", style="bold red")
                continue
            interpreter.parse_and_execute(line)
        except (KeyboardInterrupt, EOFError):
            console.print("\nSaindo do CLI (Ctrl+C / EOF).", style="bold yellow")
            break
        except Exception as e:
            console.print(f"Erro: {e}", style="bold red")

if __name__ == "__main__":
    main()
