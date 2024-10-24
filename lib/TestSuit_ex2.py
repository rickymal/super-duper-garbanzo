# Importações necessárias (assumindo que todas as classes e funcionalidades estão implementadas)
from abc import ABC, abstractmethod
from test_framework import (
    TestInstance, Container, Pipeline, Context, Alucinator, BaseOutput
)
import json
import logging


# Classe responsável por gerar o output, utilizando a lib 'rich'
class RichConsole(BaseOutput):
    pass


# Configuração do Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Definição das funções de setup e teardown
def global_setup():
    logger.info("Configurando o ambiente global de testes...")
    # Código para iniciar serviços globais, se necessário


def global_teardown():
    logger.info("Limpando o ambiente global de testes...")
    # Código para encerrar serviços globais, se necessário


# Definição das funções de teste (steps)
def send_numbers(ctx: Context):
    # Alucinador pode modificar os dados com base em critérios específicos
    ctx.alucinator(ctx.get('data')).do_something()
    ctx.set('n1', 10)
    ctx.set('n2', 20)
    logger.info("Números enviados: n1=10, n2=20")


def process_numbers(ctx: Context):
    n1 = ctx.get('n1')
    n2 = ctx.get('n2')
    result = n1 + n2
    ctx.set('result', result)
    logger.info(f"Números processados: {n1} + {n2} = {result}")


def check_result(ctx: Context):
    n1 = ctx.get('n1', 10)
    n2 = ctx.get('n2', 20)
    result = ctx.get('result')
    expected = n1 + n2
    if result == expected:
        ctx.approve()
        logger.info(f"Resultado verificado: {result} == {expected}")
    else:
        ctx.reject(f"Resultado incorreto: {result} != {expected}")
        logger.error(f"Resultado incorreto: {result} != {expected}")


def alucinador_modificar_result(ctx: Context):
    # Alucinação: modifica o resultado para um valor incorreto
    ctx.set('result', ctx.get('result') + 5)
    logger.warning("Alucinação: Resultado foi alterado para um valor incorreto")


def start_microservice(ctx: Context):
    # Código para iniciar um microserviço específico
    ctx.set('microservice', 'auth_service')
    logger.info("Microserviço 'auth_service' iniciado.")


def stop_microservice(ctx: Context):
    # Código para encerrar um microserviço específico
    microservice = ctx.get('microservice')
    if microservice:
        logger.info(f"Microserviço '{microservice}' encerrado.")
        ctx.set('microservice', None)


def check_login_success(ctx: Context):
    # Implementação fictícia para verificar sucesso de login
    success = ctx.get('login_success', True)
    if success:
        ctx.approve()
        logger.info("Login realizado com sucesso.")
    else:
        ctx.reject("Falha no login.")
        logger.error("Falha no login.")


def acessar_api(ctx: Context):
    api_url = test_instance.get_global_var('api_endpoint')
    ctx.set('api_response', f"Resposta da API em {api_url}")
    logger.info(f"Acessando API em {api_url}")


# Definição de fixtures e factories
def user_fixture():
    return {
        'username': 'test_user',
        'password': 'secure_password'
    }


def dynamic_number_factory(n1, n2):
    return {
        'n1': n1,
        'n2': n2
    }


# Classe de alucinação especial (exemplo)
class AlucinatorSpecial(Alucinator):
    def do_something(self, data):
        # Implementação específica da alucinação
        if 'n1' in data and 'n2' in data:
            data['n1'] += 1  # Exemplo de modificação
        return data


# Definição da classe BaseContainer
class BaseContainer(ABC):
    def __init__(self, name):
        self.name = name
        self.subcontainers = []
        self.pipelines = []
        self.hooks_before_each = []
        self.hooks_after_each = []
        self.fixtures = {}
        self.factories = {}
        self.annotations = {}
        self.tags = []

    def create_container(self, category: str, description: str):
        container = Container(f"{category}: {description}")
        self.subcontainers.append(container)
        return container

    def create_pipeline(self, name: str):
        pipeline = Pipeline(name)
        self.pipelines.append(pipeline)
        return pipeline

    def add_fixture(self, key, value):
        self.fixtures[key] = value

    def add_factory(self, name, factory_func, alucinator=None):
        self.factories[name] = {'func': factory_func, 'alucinator': alucinator}

    def before_each(self, func):
        self.hooks_before_each.append(func)

    def after_each(self, func):
        self.hooks_after_each.append(func)

    def add_annotation(self, key, value):
        self.annotations[key] = value

    def add_tags(self, tags):
        self.tags.extend(tags)

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def get_metrics(self):
        pass


# Definição da classe TestInstance
class TestInstance(BaseContainer):
    def __init__(self):
        super().__init__("Test Instance")

    def run(self):
        logger.info("Iniciando execução dos testes...")
        # Executa hooks before_all
        for hook in self.hooks_before_each:
            hook()

        # Executa todos os containers
        for container in self.subcontainers:
            container.execute()

        # Executa hooks after_all
        for hook in self.hooks_after_each:
            hook()

    def get_metrics(self):
        metrics = []
        for container in self.subcontainers:
            metrics.extend(container.get_metrics())
        return metrics


# Definição da classe Container
class Container(BaseContainer):
    def __init__(self, name):
        super().__init__(name)

    def execute(self):
        logger.info(f"Executando Container: {self.name}")

        # Executa hooks_before_each
        for hook in self.hooks_before_each:
            hook()

        # Executa pipelines
        for pipeline in self.pipelines:
            pipeline.execute()

        # Executa subcontainers
        for container in self.subcontainers:
            container.execute()

        # Executa hooks_after_each
        for hook in self.hooks_after_each:
            hook()

    def get_metrics(self):
        metrics = []
        for pipeline in self.pipelines:
            metrics.append(pipeline.get_metrics())
        for container in self.subcontainers:
            metrics.extend(container.get_metrics())
        return metrics


# Definição da classe Pipeline
class Pipeline(BaseContainer):
    def __init__(self, name):
        super().__init__(name)
        self.steps = []

    def add_step(self, description: str, func, **kwargs):
        step = Step(description, func, **kwargs)
        self.steps.append(step)

    def execute(self):
        logger.info(f"  Executando Pipeline: {self.name}")

        # Executa hooks_before_each
        for hook in self.hooks_before_each:
            hook()

        context = Context()

        # Executa cada step
        for step in self.steps:
            logger.info(f"    Executando Step: {step.description}")
            try:
                step.execute(context)
            except Exception as e:
                logger.error(f"      ❌ Exceção no Step '{step.description}': {e}")
                context.reject(f"Exceção: {e}")
                break

        # Executa hooks_after_each
        for hook in self.hooks_after_each:
            hook()

        # Verifica o resultado final do pipeline
        if context.approved:
            logger.info(f"    ✅ Pipeline '{self.name}' PASSOU.")
        else:
            logger.error(f"    ❌ Pipeline '{self.name}' FALHOU.")
            for error in context.errors:
                logger.error(f"      Erro: {error}")

    def get_metrics(self):
        return {
            'pipeline': self.name,
            'annotations': self.annotations,
            'tags': self.tags,
            # Adicione mais métricas conforme necessário
        }


# Definição da classe Step
class Step:
    def __init__(self, description: str, func, **kwargs):
        self.description = description
        self.func = func
        self.kwargs = kwargs

    def execute(self, context: Context):
        # Passa o contexto e quaisquer argumentos adicionais para a função
        self.func(context, **self.kwargs)


# Definição da classe Context
class Context:
    def __init__(self):
        self.data = {}
        self.approved = False
        self.errors = []

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def approve(self):
        self.approved = True

    def reject(self, error_message: str):
        self.approved = False
        self.errors.append(error_message)

    def alucinator(self, data):
        # Placeholder para o Alucinator
        return data


# Criação da instância de testes
test_instance = TestInstance()  # TestInstance é uma classe filha de BaseContainer

# Adicionando hooks de setup e teardown
test_instance.before_each(global_setup)
test_instance.after_each(global_teardown)

# Adicionando fixtures e factories
test_instance.add_fixture('user', user_fixture())
test_instance.add_factory('dynamic_numbers', dynamic_number_factory, AlucinatorSpecial())  # Adicionando AlucinatorSpecial à factory

# Criação de múltiplos containers de testes
container_base = test_instance.create_container("Cenário", "Cenário Base de Teste")
container_login = test_instance.create_container("Cenário", "Cenário de Login")

# Adicionando hooks em containers
container_login.before_each(lambda: print("Hook before_each no Cenário de Login"))
sub_description_login = container_login.create_container('Subdescrição', 'Uma sub-descrição para o login')
sub_description_login.before_each(lambda: print("Hook before_each na Subdescrição de Login"))

description_jornada = container_base.create_container('Subdescrição', 'Simular a jornada do usuário')
sub_description_jornada = description_jornada.create_container('Subdescrição', 'Uma sub-descrição para a jornada')

# Criação de pipelines com steps dentro do container de jornada
pipeline_soma = sub_description_jornada.create_pipeline('Deve ser capaz de somar dois números')

# Adicionando hooks no pipeline
pipeline_soma.before_each(lambda: print("Hook before_each no Pipeline Soma"))

# Adicionando steps ao pipeline
pipeline_soma.add_step('Enviando os números', send_numbers)
pipeline_soma.add_step('Processando os números', process_numbers)
pipeline_soma.add_step('Verificando resultados', check_result)

# Pipeline com alucinação
pipeline_alucinacao = sub_description_jornada.create_pipeline('Testar comportamento com alucinação')
pipeline_alucinacao.add_step('Enviando os números', send_numbers, alucinator=AlucinatorSpecial())  # Injetando AlucinatorSpecial para ser recuperado no 'ctx'
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

# Adicionando tags e anotações aos pipelines
pipeline_soma.add_annotation('priority', 'high')
pipeline_soma.add_annotation('author', 'Rickymal')
pipeline_alucinacao.add_annotation('priority', 'medium')
pipeline_alucinacao.add_annotation('author', 'Rickymal')
pipeline_microservice.add_annotation('priority', 'critical')
pipeline_microservice.add_annotation('author', 'Rickymal')

pipeline_soma.add_tags(['soma', 'calculadora'])
pipeline_alucinacao.add_tags(['alucinacao', 'teste_de_resiliencia'])
pipeline_microservice.add_tags(['microservice', 'auth_service'])

# Definição de pipelines parametrizados
dados_parametrizados = [
    {'n1': 5, 'n2': 15},
    {'n1': 20, 'n2': 30},
    {'n1': 0, 'n2': 0},
]

for dados in dados_parametrizados:
    pipeline = sub_description_jornada.create_pipeline(f'Somar {dados["n1"]} + {dados["n2"]}')

    # Função para configurar os dados do contexto usando a factory
    def setup_numbers(ctx: Context, d=dados):
        numbers = test_instance.create_from_factory('dynamic_numbers', d['n1'], d['n2'])
        ctx.set('n1', numbers['n1'])
        ctx.set('n2', numbers['n2'])
        logger.info(f"Números enviados: n1={numbers['n1']}, n2={numbers['n2']}")

    pipeline.add_step('Enviando os números', setup_numbers)
    pipeline.add_step('Processando os números', process_numbers)
    pipeline.add_step('Verificando resultados', check_result)

# Uso de Fixtures em um Pipeline de Login
def perform_login(ctx: Context):
    user = test_instance.get_fixture('user')
    ctx.set('username', user['username'])
    ctx.set('password', user['password'])
    # Simular login (exemplo fictício)
    if user['username'] == 'test_user' and user['password'] == 'secure_password':
        ctx.set('login_success', True)
        logger.info("Login realizado com sucesso.")
    else:
        ctx.set('login_success', False)
        logger.error("Falha no login.")


pipeline_login = sub_description_login.create_pipeline('Deve realizar login com usuário válido')
pipeline_login.add_step('Realizando login', perform_login)
pipeline_login.add_step('Verificando login', check_login_success)

# Pipeline que utiliza uma Factory para números dinâmicos
pipeline_dynamic = sub_description_jornada.create_pipeline('Deve ser capaz de somar números dinamicamente')
pipeline_dynamic.add_step('Enviando os números', setup_numbers)  # Reutilizando a função setup_numbers
pipeline_dynamic.add_step('Processando os números', process_numbers)
pipeline_dynamic.add_step('Verificando resultados', check_result)

# Pipeline que acessa a API utilizando variável global
pipeline_api = sub_description_jornada.create_pipeline('Deve ser capaz de acessar a API')
pipeline_api.add_step('Acessando a API', acessar_api)
pipeline_api.add_step('Verificando resposta da API', lambda ctx: (
    ctx.approve() if 'Resposta da API' in ctx.get('api_response') else ctx.reject("Resposta da API inválida")
))

# Adicionando variáveis globais
test_instance.set_global_var('api_endpoint', 'https://api.test.example.com')

# Execução dos testes
test_instance.run()

# Salvando métricas
metrics = test_instance.get_metrics()  # Supondo que exista um método para obter as métricas
with open('metrics.json', 'w') as f:
    json.dump(metrics, f, indent=4)

# Integração com Sistema de Monitoramento e Alertas
def send_alert(message: str):
    # Código para enviar alerta (e.g., via Slack, Email, etc.)
    logger.info(f"Alerta: {message}")


# Verificação das métricas e envio de alertas se necessário
for metric in metrics:
    if metric['status'] == 'FAILED':
        send_alert(f"Teste '{metric['pipeline']}' falhou com o erro: {metric['error']}")

# Salvando métricas atualizadas após execuções adicionais
metrics_updated = test_instance.get_metrics()
with open('metrics_updated.json', 'w') as f:
    json.dump(metrics_updated, f, indent=4)
