# example_tests.py

# Importando o módulo test_flow
from test_flow import (
    TestInstance, Alucinator, Context, RichConsole
)
import random

# Instância do Output
output = RichConsole()

# Criação da instância de testes
test_instance = TestInstance(output)

# Adicionando hooks de setup e teardown
def global_setup():
    output.log("Executando o setup global dos testes...")

def global_teardown():
    output.log("Executando o teardown global dos testes...")

test_instance.before_each(global_setup)
test_instance.after_each(global_teardown)

# Adicionando variáveis globais
test_instance.set_global_var('api_endpoint', 'https://api.exemplo.com')

# Adicionando fixtures e factories
def user_fixture():
    return {'username': 'usuario_teste', 'password': 'senha_segura'}

def random_number_factory():
    return {'n1': random.randint(1, 100), 'n2': random.randint(1, 100)}

test_instance.add_fixture('user', user_fixture())
test_instance.add_factory('random_numbers', random_number_factory)

# Criando um Alucinator personalizado
class CustomAlucinator(Alucinator):
    def do_something(self, data):
        # Introduzindo uma falha proposital nos dados
        if 'n1' in data:
            data['n1'] = data['n1'] * -1  # Invertendo o sinal do número
        return data

# Criando containers e pipelines
main_container = test_instance.create_container('Cenário', 'Testes Principais')

# Adicionando um pipeline simples
pipeline_simples = main_container.create_pipeline('Teste de Soma Simples')

def enviar_numeros(ctx: Context):
    numeros = test_instance.get_factory('random_numbers')['func']()
    ctx.set('n1', numeros['n1'])
    ctx.set('n2', numeros['n2'])
    ctx.output.log(f"Números enviados: n1={numeros['n1']}, n2={numeros['n2']}")
    ctx.approve()

def somar_numeros(ctx: Context):
    n1 = ctx.get('n1')
    n2 = ctx.get('n2')
    resultado = n1 + n2
    ctx.set('resultado', resultado)
    ctx.output.log(f"Resultado da soma: {n1} + {n2} = {resultado}")
    ctx.approve()

def verificar_resultado(ctx: Context):
    n1 = ctx.get('n1')
    n2 = ctx.get('n2')
    resultado = ctx.get('resultado')
    if resultado == n1 + n2:
        ctx.approve()
        ctx.output.log("Resultado verificado com sucesso.")
    else:
        ctx.reject("Resultado incorreto.")
        ctx.output.log("Falha na verificação do resultado.")

pipeline_simples.add_step('Enviar Números', enviar_numeros)
pipeline_simples.add_step('Somar Números', somar_numeros)
pipeline_simples.add_step('Verificar Resultado', verificar_resultado)

# Adicionando um pipeline com alucinação
pipeline_alucinado = main_container.create_pipeline('Teste com Alucinação')

pipeline_alucinado.add_step('Enviar Números', enviar_numeros, alucinator=CustomAlucinator())
pipeline_alucinado.add_step('Somar Números', somar_numeros)
pipeline_alucinado.add_step('Verificar Resultado', verificar_resultado)

# Adicionando um pipeline que simula um login
pipeline_login = main_container.create_pipeline('Teste de Login')

def realizar_login(ctx: Context):
    user = test_instance.get_fixture('user')
    ctx.set('username', user['username'])
    ctx.set('password', user['password'])
    ctx.output.log(f"Tentando login com usuário: {user['username']}")
    if user['username'] == 'usuario_teste' and user['password'] == 'senha_segura':
        ctx.set('login_sucesso', True)
        ctx.approve()
        ctx.output.log("Login realizado com sucesso.")
    else:
        ctx.set('login_sucesso', False)
        ctx.reject("Falha no login.")
        ctx.output.log("Não foi possível realizar o login.")

def verificar_login(ctx: Context):
    if ctx.get('login_sucesso'):
        ctx.approve()
        ctx.output.log("Verificação de login bem-sucedida.")
    else:
        ctx.reject("Login não realizado.")
        ctx.output.log("Falha na verificação do login.")

pipeline_login.add_step('Realizar Login', realizar_login)
pipeline_login.add_step('Verificar Login', verificar_login)

# Adicionando um pipeline que acessa uma API
pipeline_api = main_container.create_pipeline('Teste de Acesso à API')

def acessar_api(ctx: Context):
    api_endpoint = test_instance.get_global_var('api_endpoint')
    ctx.output.log(f"Acessando API em {api_endpoint}")
    # Simulando uma resposta da API
    ctx.set('api_response', {'status_code': 200, 'data': {'message': 'Sucesso'}})
    ctx.approve()

def verificar_resposta_api(ctx: Context):
    resposta = ctx.get('api_response')
    if resposta and resposta['status_code'] == 200:
        ctx.approve()
        ctx.output.log("API respondeu com sucesso.")
    else:
        ctx.reject("Falha na resposta da API.")
        ctx.output.log("API não respondeu conforme esperado.")

pipeline_api.add_step('Acessar API', acessar_api)
pipeline_api.add_step('Verificar Resposta da API', verificar_resposta_api)

# Adicionando um pipeline com testes Monte Carlo
NUM_TESTES_MONTE_CARLO = 5

for i in range(NUM_TESTES_MONTE_CARLO):
    pipeline_monte_carlo = main_container.create_pipeline(f'Teste Monte Carlo #{i+1}')
    
    def setup_numeros_aleatorios(ctx: Context):
        numeros = test_instance.get_factory('random_numbers')['func']()
        ctx.set('n1', numeros['n1'])
        ctx.set('n2', numeros['n2'])
        ctx.output.log(f"Números aleatórios gerados: n1={numeros['n1']}, n2={numeros['n2']}")
        ctx.approve()
    
    pipeline_monte_carlo.add_step('Gerar Números Aleatórios', setup_numeros_aleatorios)
    pipeline_monte_carlo.add_step('Somar Números', somar_numeros)
    pipeline_monte_carlo.add_step('Verificar Resultado', verificar_resultado)

# Executando os testes
test_instance.run()

# Salvando métricas
metrics = test_instance.get_metrics()
with open('metrics.json', 'w') as f:
    json.dump(metrics, f, indent=4)

# Enviando alertas se houver falhas
def send_alert(message: str):
    output.log(f"Alerta: {message}")

for metric in metrics:
    if metric.get('status') == 'FAILED':
        send_alert(f"Teste '{metric.get('pipeline')}' falhou com o erro: {metric.get('errors')}")
