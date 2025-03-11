from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Dict, Any, Tuple

app = FastAPI()

# =============================================================================
# 1. CONTEXTO DE APLICAÇÃO E REGISTRIES
# =============================================================================

class ApplicationContext:
    def __init__(self, data: Dict[str, Any]):
        """
        data pode conter quaisquer chaves que você precisa
        para cálculos (p. ex., 'years': ('2023','2024')).
        """
        self.data = data

    def get(self, key: str):
        return self.data.get(key)

    def date_interval(self, years: Tuple[str, str]):
        """
        Retorna True se o intervalo de anos especificado
        estiver incluso na estrutura de dados do contexto.
        """
        start, end = years
        return start in self.data.get("years", []) and end in self.data.get("years", [])


registry = {
    "investments": {},
    "users": {},
    "views": {}
}


def investment(name):
    """
    Decorador para registrar um investimento com determinado 'name'.
    A função decorada deve aceitar um 'ApplicationContext' como parâmetro.
    """
    def decorator(func):
        registry["investments"][name] = func
        return func
    return decorator


def user(name):
    """
    Decorador para registrar um usuário.
    A função deve retornar um dicionário contendo pelo menos:
    {
      'salary': ...,
      'investments': [lista de functions de investimentos],
      'view': [lista de functions de views]
    }
    """
    def decorator(func):
        registry["users"][name] = func
        return func
    return decorator


def view(type_, name, desc):
    """
    Decorador para registrar uma 'view' (visualização).
    Pode ser do tipo 'table', 'text', etc. Recebe uma breve descrição.
    """
    def decorator(func):
        registry["views"][name] = {
            "type": type_,
            "desc": desc,
            "func": func
        }
        return func
    return decorator

# =============================================================================
# 2. EXEMPLOS DE USO
# =============================================================================

@investment(name='selic')
def selic(ctx: ApplicationContext):
    """
    Retorna o valor da Selic, variando de acordo com o intervalo de datas.
    """
    if ctx.date_interval(('2024','2025')):
        return 0.13
    return 0.15


@investment(name='cdb')
def cdb(ctx: ApplicationContext):
    """
    Retorna o valor do CDB, dependendo da Selic e do intervalo de anos.
    """
    if ctx.date_interval(('2023','2024')):
        # Pegamos o valor da selic previamente calculado ou default
        selic_value = ctx.get('selic_value')
        if selic_value is not None:
            return 0.8 * selic_value
    # Valor default, se não estiver no intervalo
    return 0.10


@view(type_='table', name='projection', desc='Projeção para o futuro')
def projection(ctx: ApplicationContext):
    """
    Exemplo de uma view que retorna uma projeção em formato de tabela (dict).
    """
    # Suponha que queremos projetar o futuro_value com base em algum cálculo
    # simples. Aqui apenas retornamos algo fixo como exemplo.
    return {
        "description": "Projeção de valores para o futuro",
        "future_value": 10000
    }


@view(type_='text', name='VaR', desc='Value at Risk')
def VaR(ctx: ApplicationContext):
    """
    Exemplo de uma view que retorna um texto simples sobre risco.
    """
    return "Risco de perda estimado em 5%."


@user(name='henrique')
def henrique():
    """
    Informações do usuário 'henrique', incluindo investimentos e views de interesse.
    """
    return {
        "salary": 5000,
        "investments": [selic, cdb],     # Referências diretas às funções dos investimentos
        "view": [projection, VaR]       # Referências diretas às funções das views
    }

# =============================================================================
# 3. CRIAÇÃO DOS ENDPOINTS DINÂMICOS COM FASTAPI
# =============================================================================

@app.get("/users")
def list_users():
    """
    Lista todos os usuários registrados via decorator.
    """
    return {"users": list(registry["users"].keys())}


@app.get("/users/{user_name}")
def get_user_info(user_name: str):
    """
    Exibe as informações básicas de um usuário (salary, lista de investimentos, views, etc.).
    """
    user_func = registry["users"].get(user_name)
    if not user_func:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user_data = user_func()
    # Transformamos a lista de referências de função em nomes (para exibir)
    investments_names = []
    for inv_func in user_data["investments"]:
        # Percorremos o dicionário de registry para achar a key
        for key, val in registry["investments"].items():
            if val == inv_func:
                investments_names.append(key)

    view_names = []
    for view_func in user_data["view"]:
        for key, val in registry["views"].items():
            if val["func"] == view_func:
                view_names.append(key)

    return {
        "salary": user_data["salary"],
        "investments": investments_names,
        "views": view_names
    }


@app.get("/users/{user_name}/investments")
def calculate_investments(
    user_name: str,
    start_year: Optional[str] = Query(None),
    end_year: Optional[str] = Query(None)
):
    """
    Calcula o valor dos investimentos de um usuário, permitindo passar um
    intervalo de datas via query params (por ex. ?start_year=2024&end_year=2025).
    """
    user_func = registry["users"].get(user_name)
    if not user_func:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user_data = user_func()

    # Criamos o contexto de aplicação
    # Caso o usuário informe start_year e end_year, inserimos em 'years'
    years = []
    if start_year and end_year:
        years = [start_year, end_year]

    ctx_data = {
        "years": years
    }

    # Para aproveitar dependências (Ex: cdb depende de selic), podemos calcular
    # selic primeiro e armazenar em ctx_data, depois passamos esse valor.
    # Supondo que a ordem [selic, cdb] importe:
    results = {}
    for inv_func in user_data["investments"]:
        # Primeiro precisamos descobrir o "nome" do investimento no registry
        inv_name = None
        for k, v in registry["investments"].items():
            if v == inv_func:
                inv_name = k
                break

        # Calculamos valor do investimento (passo 1: se for a selic)
        value = None
        # Exemplo: se for a selic, guardamos 'selic_value' no contexto
        if inv_name == 'selic':
            value = inv_func(ApplicationContext(ctx_data))
            ctx_data['selic_value'] = value
        else:
            # Passamos a selic_value como parte do ctx, caso o investimento precise
            value = inv_func(ApplicationContext(ctx_data))

        results[inv_name] = value

    return results


@app.get("/users/{user_name}/views")
def list_user_views(user_name: str):
    """
    Lista as views disponíveis para um usuário.
    """
    user_func = registry["users"].get(user_name)
    if not user_func:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user_data = user_func()
    views_info = []
    for view_func in user_data["view"]:
        for key, val in registry["views"].items():
            if val["func"] == view_func:
                views_info.append({
                    "name": key,
                    "type": val["type"],
                    "desc": val["desc"]
                })

    return {"views": views_info}


@app.get("/users/{user_name}/views/{view_name}")
def run_user_view(
    user_name: str,
    view_name: str,
    start_year: Optional[str] = Query(None),
    end_year: Optional[str] = Query(None)
):
    """
    Executa uma 'view' específica para um usuário, opcionalmente usando
    intervalos de anos passados em query params.
    """
    user_func = registry["users"].get(user_name)
    if not user_func:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user_data = user_func()
    # Verificamos se o usuário tem a view desejada
    target_view_func = None
    for vf in user_data["view"]:
        # Descobrindo o "nome" da função de view
        for key, val in registry["views"].items():
            if val["func"] == vf and key == view_name:
                target_view_func = vf
                break

    if not target_view_func:
        raise HTTPException(status_code=404, detail="View não encontrada para esse usuário.")

    # Cria o contexto
    years = []
    if start_year and end_year:
        years = [start_year, end_year]

    ctx_data = {
        "years": years
    }
    result = target_view_func(ApplicationContext(ctx_data))
    return {"view_name": view_name, "result": result}
