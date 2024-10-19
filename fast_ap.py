from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

# Configuração do Rich
console = Console()

# Classe de gerenciamento de testes
class ServerTesting:
    def __init__(self):
        self.suites = []

    def describe(self, description):
        suite = TestSuite(description)
        self.suites.append(suite)
        return suite

    def run(self):
        table = Table(title="Test Results", show_header=True, header_style="bold magenta")
        table.add_column("Test Suite", style="dim")
        table.add_column("Test", justify="left")
        table.add_column("Status", justify="center")

        # Barra de progresso para os testes
        with Progress() as progress:
            task = progress.add_task("[cyan]Running tests...", total=len(self.suites))
            results = []
            for suite in self.suites:
                result = suite.run(table)
                results.append(result)
                progress.advance(task)
        console.print(Panel(table))
        return results

class TestSuite:
    def __init__(self, description):
        self.description = description
        self.tests = []

    def it(self, test_description):
        def wrapper(func):
            self.tests.append((test_description, func))
            return func
        return wrapper

    def run(self, table):
        suite_results = []
        for test_description, test_func in self.tests:
            try:
                test_func(None)
                table.add_row(self.description, test_description, "[green]✔ Passed")
                suite_results.append({"test": test_description, "status": "Passed"})
            except AssertionError as e:
                table.add_row(self.description, test_description, "[red]✘ Failed")
                suite_results.append({"test": test_description, "status": "Failed", "error": str(e)})
        return suite_results

# Definindo a API com FastAPI
app = FastAPI()
serverTesting = ServerTesting()

# Modelo para o frontend solicitar a execução de testes
class TestRequest(BaseModel):
    description: str
    tests: list

@app.post("/run-tests/")
async def run_tests(test_request: TestRequest):
    description = serverTesting.describe(test_request.description)
    
    # Adicionando cada teste à suite
    for test in test_request.tests:
        @description.it(test["name"])
        def run_test(context):
            exec(test["code"])  # Executa o código de teste
    
    # Executa os testes com Rich
    results = serverTesting.run()
    return JSONResponse(content={"status": "completed", "results": results})

@app.get("/tests/")
async def get_tests():
    # Executa os testes definidos
    results = serverTesting.run()
    return JSONResponse(content={"results": results})

# Definindo alguns testes manuais
description = serverTesting.describe("Operações Matemáticas")

@description.it("deve somar dois números")
def test_sumNumbers(context):
    assert 1 + 1 == 2

@description.it("deve subtrair dois números")
def test_subtractNumbers(context):
    assert 2 - 1 == 0

if __name__ == "__main__":
    serverTesting.run()
    # import uvicorn
    # uvicorn.run(app, host="127.0.0.1", port=8000)
