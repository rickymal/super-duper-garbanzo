# Importações necessárias
from abc import ABC, abstractmethod
import json
import logging
import random
from rich.console import Console
from rich.tree import Tree
from rich.table import Table
import time
import random

# Configuração do Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Classe BaseOutput (para gerenciamento de saída)
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




# Classe Alucinator
class Alucinator:
    def do_something(self, data):
        return data

# Classe Context
class Context:
    def __init__(self, output):
        self.data = {}
        self.approved = False
        self.errors = []
        self.container = None
        self.alucinator = None
        self.output = output

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def approve(self):
        self.approved = True

    def reject(self, error_message: str):
        self.approved = False
        self.errors.append(error_message)

# Classe Step
class Step:
    def __init__(self, description: str, func, **kwargs):
        self.description = description
        self.func = func
        self.kwargs = kwargs

    def execute(self, context: Context):
        context.output.start_step(self)
        try:
            alucinator = self.kwargs.get('alucinator')
            if alucinator:
                context.alucinator = alucinator
            else:
                context.alucinator = None
            context.step_description = self.description
            self.func(context, **self.kwargs)
            status = "PASSED" if context.approved else "FAILED"
            context.output.end_step(self, status)
        except Exception as e:
            context.reject(f"Exceção no Step '{self.description}': {e}")
            context.output.end_step(self, "FAILED")
            raise e


class IExecutable(ABC):
    @abstractmethod
    def execute(self):
        pass

# Classe BaseContainer
class IBaseContainer(ABC):
    def __init__(self, name, output):
        self.name = name
        self.subcontainers = []
        self.pipelines = []
        self.hooks_before_each = []
        self.hooks_after_each = []
        self.fixtures = {}
        self.factories = {}
        self.annotations = {}
        self.tags = []
        self.parent = None
        self.output = output

    def create_container(self, category: str, description: str):
        container = Container(f"{category}: {description}", self.output)
        container.parent = self
        self.subcontainers.append(container)
        return container

    def create_pipeline(self, name: str):
        pipeline = Pipeline(name, self.output)
        pipeline.parent = self
        self.pipelines.append(pipeline)
        return pipeline

    def add_fixture(self, key, value):
        self.fixtures[key] = value

    def get_fixture(self, key, default=None):
        if key in self.fixtures:
            return self.fixtures[key]
        elif self.parent:
            return self.parent.get_fixture(key, default)
        else:
            return default

    def add_factory(self, name, factory_func, alucinator=None):
        self.factories[name] = {'func': factory_func, 'alucinator': alucinator}

    def get_factory(self, name):
        if name in self.factories:
            return self.factories[name]
        elif self.parent:
            return self.parent.get_factory(name)
        else:
            return None

    def before_each(self, func):
        self.hooks_before_each.append(func)

    def after_each(self, func):
        self.hooks_after_each.append(func)

    def add_annotation(self, key, value):
        self.annotations[key] = value

    def add_tags(self, tags):
        self.tags.extend(tags)

    @abstractmethod
    def get_metrics(self):
        pass

# Classe TestInstance
class TestInstance(IBaseContainer):
    def __init__(self, output):
        super().__init__("Test Instance", output)
        self.global_vars = {}
        self.global_fixtures = {}
        self.global_hooks_before_all = []
        self.global_hooks_after_all = []

    def set_global_var(self, key, value):
        self.global_vars[key] = value

    def get_global_var(self, key, default=None):
        return self.global_vars.get(key, default)

    def add_global_fixture(self, key, value):
        self.global_fixtures[key] = value

    def get_fixture(self, key, default=None):
        if key in self.fixtures:
            return self.fixtures[key]
        elif key in self.global_fixtures:
            return self.global_fixtures[key]
        else:
            return default

    def before_all(self, func):
        self.global_hooks_before_all.append(func)

    def after_all(self, func):
        self.global_hooks_after_all.append(func)

    def run(self):
        self.output.start_test_instance(self)
        for hook in self.global_hooks_before_all:
            hook()
        for hook in self.hooks_before_each:
            hook()
        for container in self.subcontainers:
            container.execute()
        for hook in self.hooks_after_each:
            hook()
        for hook in self.global_hooks_after_all:
            hook()
        self.output.end_test_instance(self)

    def get_metrics(self):
        metrics = []
        for container in self.subcontainers:
            metrics.extend(container.get_metrics())
        return metrics

# Classe Container
class Container(IBaseContainer, IExecutable):
    def __init__(self, name, output):
        super().__init__(name, output)

    def execute(self):
        self.output.start_container(self)
        for hook in self.hooks_before_each:
            hook()
        for pipeline in self.pipelines:
            pipeline.execute()
        for container in self.subcontainers:
            container.execute()
        for hook in self.hooks_after_each:
            hook()
        self.output.end_container(self)

    def get_metrics(self):
        metrics = []
        for pipeline in self.pipelines:
            metrics.append(pipeline.get_metrics())
        for container in self.subcontainers:
            metrics.extend(container.get_metrics())
        return metrics

# Classe Pipeline
class Pipeline(IBaseContainer, IExecutable):
    def __init__(self, name, output):
        super().__init__(name, output)
        self.steps = []
        self.parent = None
        self.last_context = None

    def add_step(self, description: str, func, **kwargs):
        step = Step(description, func, **kwargs)
        self.steps.append(step)

    def execute(self):
        self.output.start_pipeline(self)
        for hook in self.hooks_before_each:
            hook()
        self.last_context = Context(self.output)
        self.last_context.container = self
        for step in self.steps:
            try:
                step.execute(self.last_context)
                if not self.last_context.approved:
                    break
            except Exception as e:
                logger.error(f"Exceção no Step '{step.description}': {e}")
                break
        for hook in self.hooks_after_each:
            hook()
        status = "PASSED" if self.last_context.approved else "FAILED"
        self.output.end_pipeline(self, status)

    def get_metrics(self):
        status = 'PASSED' if self.last_context and self.last_context.approved else 'FAILED'
        errors = '; '.join(self.last_context.errors) if self.last_context and self.last_context.errors else None
        return {
            'pipeline': self.name,
            'status': status,
            'errors': errors,
            'annotations': self.annotations,
            'tags': self.tags,
        }

# Funções de setup e teardown
def global_setup():
    logger.info("Configurando o ambiente global de testes...")

def global_teardown():
    logger.info("Limpando o ambiente global de testes...")

# Funções de teste (steps)
def send_numbers(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))  # Atraso entre 1 e 2 segundos
    if ctx.alucinator:
        data = ctx.data.copy()
        data = ctx.alucinator.do_something(data)
        ctx.data.update(data)
    ctx.set('n1', ctx.get('n1', 10))
    ctx.set('n2', ctx.get('n2', 20))
    ctx.output.log(f"Números enviados: n1={ctx.get('n1')}, n2={ctx.get('n2')}")
    ctx.approve()

def process_numbers(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    n1 = ctx.get('n1')
    n2 = ctx.get('n2')
    result = n1 + n2
    ctx.set('result', result)
    ctx.output.log(f"Números processados: {n1} + {n2} = {result}")
    ctx.approve()

def check_result(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    n1 = ctx.get('n1', 10)
    n2 = ctx.get('n2', 20)
    result = ctx.get('result')
    expected = n1 + n2
    if result == expected:
        ctx.approve()
        ctx.output.log(f"Resultado verificado: {result} == {expected}")
    else:
        ctx.reject(f"Resultado incorreto: {result} != {expected}")
        ctx.output.log(f"Resultado incorreto: {result} != {expected}")

def alucinador_modificar_result(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    ctx.set('result', ctx.get('result') + 5)
    ctx.output.log("Alucinação: Resultado foi alterado para um valor incorreto")
    ctx.approve()

def start_microservice(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    ctx.set('microservice', 'auth_service')
    ctx.output.log("Microserviço 'auth_service' iniciado.")
    ctx.approve()

def stop_microservice(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    microservice = ctx.get('microservice')
    if microservice:
        ctx.output.log(f"Microserviço '{microservice}' encerrado.")
        ctx.set('microservice', None)
    ctx.approve()

def check_login_success(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    success = ctx.get('login_success', True)
    if success:
        ctx.approve()
        ctx.output.log("Login realizado com sucesso.")
    else:
        ctx.reject("Falha no login.")
        ctx.output.log("Falha no login.")

def acessar_api(ctx: Context, **kwargs):
    time.sleep(random.uniform(1, 2))
    api_url = ctx.container.get_global_var('api_endpoint')
    ctx.set('api_response', f"Resposta da API em {api_url}")
    ctx.output.log(f"Acessando API em {api_url}")
    ctx.approve()

# Fixtures e Factories
def user_fixture():
    return {
        'username': 'test_user',
        'password': 'secure_password'
    }

def dynamic_number_factory():
    n1 = random.randint(0, 100)
    n2 = random.randint(0, 100)
    return {'n1': n1, 'n2': n2}

def generate_random_numbers():
    n1 = random.randint(0, 100)
    n2 = random.randint(0, 100)
    return {'n1': n1, 'n2': n2}

def generate_user_load():
    return {'user_load': random.randint(50, 500)}

def generate_response_time():
    return {'response_time': np.random.normal(loc=200, scale=50)}

def generate_random_params():
    numbers = generate_random_numbers()
    user_load = generate_user_load()
    response_time = generate_response_time()
    combined = {**numbers, **user_load, **response_time}
    return combined

# Classe AlucinatorSpecial
class AlucinatorSpecial(Alucinator):
    def do_something(self, data):
        if 'n1' in data and 'n2' in data:
            data['n1'] += 1
        return data




if __name__ == "__main__":
    # Instância do Output
    output = RichConsole()

    # Criação da instância de testes
    test_instance = TestInstance(output)

    # Adicionando hooks de setup e teardown
    test_instance.before_each(global_setup)
    test_instance.after_each(global_teardown)

    # Adicionando fixtures e factories
    test_instance.add_fixture('user', user_fixture())
    test_instance.add_factory('dynamic_numbers', dynamic_number_factory, AlucinatorSpecial())
    test_instance.add_factory('combined_params', generate_random_params, AlucinatorSpecial())

    # Criação de containers e pipelines
    container_base = test_instance.create_container("Cenário", "Cenário Base de Teste")
    container_login = test_instance.create_container("Cenário", "Cenário de Login")

    container_login.before_each(lambda: output.log("Hook before_each no Cenário de Login"))
    sub_description_login = container_login.create_container('Subdescrição', 'Uma sub-descrição para o login')
    sub_description_login.before_each(lambda: output.log("Hook before_each na Subdescrição de Login"))

    description_jornada = container_base.create_container('Subdescrição', 'Simular a jornada do usuário')
    sub_description_jornada = description_jornada.create_container('Subdescrição', 'Uma sub-descrição para a jornada')

    # Pipeline de soma
    pipeline_soma = sub_description_jornada.create_pipeline('Deve ser capaz de somar dois números')
    pipeline_soma.before_each(lambda: output.log("Hook before_each no Pipeline Soma"))
    pipeline_soma.add_step('Enviando os números', send_numbers)
    pipeline_soma.add_step('Processando os números', process_numbers)
    pipeline_soma.add_step('Verificando resultados', check_result)

    # Pipeline com alucinação
    pipeline_alucinacao = sub_description_jornada.create_pipeline('Testar comportamento com alucinação')
    pipeline_alucinacao.add_step('Enviando os números', send_numbers, alucinator=AlucinatorSpecial())
    pipeline_alucinacao.add_step('Processando os números', process_numbers)
    pipeline_alucinacao.add_step('Alucinando o resultado', alucinador_modificar_result)
    pipeline_alucinacao.add_step('Verificando resultados', check_result)

    # Pipeline que controla microserviços
    pipeline_microservice = sub_description_jornada.create_pipeline('Testar controle de microserviços')
    pipeline_microservice.add_step('Iniciando microserviço', start_microservice)
    pipeline_microservice.add_step('Enviando os números', send_numbers)
    pipeline_microservice.add_step('Processando os números', process_numbers)
    pipeline_microservice.add_step('Verificando resultados', check_result)
    pipeline_microservice.add_step('Encerrando microserviço', stop_microservice)

    # Adicionando anotações e tags
    pipeline_soma.add_annotation('priority', 'high')
    pipeline_soma.add_annotation('author', 'Rickymal')
    pipeline_alucinacao.add_annotation('priority', 'medium')
    pipeline_alucinacao.add_annotation('author', 'Rickymal')
    pipeline_microservice.add_annotation('priority', 'critical')
    pipeline_microservice.add_annotation('author', 'Rickymal')

    pipeline_soma.add_tags(['soma', 'calculadora'])
    pipeline_alucinacao.add_tags(['alucinacao', 'teste_de_resiliencia'])
    pipeline_microservice.add_tags(['microservice', 'auth_service'])

    # Pipelines parametrizados via Monte Carlo
    NUM_SCENARIOS = 10  # Ajuste conforme necessário
    import time

    def setup_combined_params(ctx: Context, factory_name='combined_params', **kwargs):
        time.sleep(2)
        factory = ctx.container.get_factory(factory_name)
        if not factory:
            ctx.reject(f"Factory '{factory_name}' não registrada.")
            return
        data = factory['func']()
        if factory.get('alucinator'):
            data = factory['alucinator'].do_something(data)
        for key, value in data.items():
            ctx.set(key, value)
        ctx.output.log(f"Parâmetros gerados: {data}")
        ctx.approve()

    for i in range(NUM_SCENARIOS):
        pipeline = sub_description_jornada.create_pipeline(f'Somar Monte Carlo {i+1}')
        pipeline.add_step('Configurar Parâmetros', setup_combined_params)
        pipeline.add_step('Enviando os números', send_numbers)
        pipeline.add_step('Processando os números', process_numbers)
        pipeline.add_step('Verificando resultados', check_result)
        if random.random() < 0.1:
            pipeline.add_step('Alucinando o resultado', alucinador_modificar_result)

    # Pipeline de login
    def perform_login(ctx: Context, **kwargs):
        user = ctx.container.get_fixture('user')
        if not user:
            ctx.reject("Fixture 'user' não encontrada.")
            return
        ctx.set('username', user['username'])
        ctx.set('password', user['password'])
        if user['username'] == 'test_user' and user['password'] == 'secure_password':
            ctx.set('login_success', True)
            ctx.output.log("Login realizado com sucesso.")
        else:
            ctx.set('login_success', False)
            ctx.reject("Falha no login.")

    pipeline_login = sub_description_login.create_pipeline('Deve realizar login com usuário válido')
    pipeline_login.add_step('Realizando login', perform_login)
    pipeline_login.add_step('Verificando login', check_login_success)

    # Pipeline que acessa a API
    pipeline_api = sub_description_jornada.create_pipeline('Deve ser capaz de acessar a API')
    pipeline_api.add_step('Acessando a API', acessar_api)
    pipeline_api.add_step('Verificando resposta da API', lambda ctx, **kwargs: (
        ctx.approve() if 'Resposta da API' in ctx.get('api_response') else ctx.reject("Resposta da API inválida")
    ))

    # Adicionando variável global
    test_instance.set_global_var('api_endpoint', 'https://api.test.example.com')

    # Execução dos testes
    test_instance.run()

    # Salvando métricas
    metrics = test_instance.get_metrics()
    with open('metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)

    # Integração com Sistema de Monitoramento e Alertas
    def send_alert(message: str):
        output.log(f"Alerta: {message}")

    # Verificação das métricas e envio de alertas se necessário
    for metric in metrics:
        if metric.get('status') == 'FAILED':
            send_alert(f"Teste '{metric.get('pipeline')}' falhou com o erro: {metric.get('errors')}")

    # Salvando métricas atualizadas após execuções adicionais
    metrics_updated = test_instance.get_metrics()
    with open('metrics_updated.json', 'w') as f:
        json.dump(metrics_updated, f, indent=4)
