import os
import signal
import time
from subprocess import Popen

import psycopg2
from psycopg2 import OperationalError

import os
import sys


def kill_process_by_port(port):
    try:
        # Encontra o PID do processo que está usando a porta
        if sys.platform == 'win32':
            # Comando para Windows
            command = f"netstat -ano | findstr :{port}"
            result = os.popen(command).read()
            if not result:
                print(f"Nenhum processo encontrado usando a porta {port}")
                return

            # Extrai o PID
            pid = result.strip().split()[-1]
            kill_command = f"taskkill /PID {pid} /F"
        else:
            # Comando para Linux/MacOS
            command = f"lsof -i :{port} | grep LISTEN"
            result = os.popen(command).read()
            if not result:
                print(f"Nenhum processo encontrado usando a porta {port}")
                return

            # Extrai o PID
            pid = result.split()[1]
            kill_command = f"kill -9 {pid}"

        # Executa o comando para matar o processo
        os.system(kill_command)
        print(f"Processo com PID {pid} usando a porta {port} foi encerrado.")

    except Exception as e:
        print(f"Ocorreu um erro ao tentar encerrar o processo na porta {port}: {e}")


# Exemplo de uso:
# kill_process_by_port(8080)

def kill_process_by_object(log, process):
    """
    Mata o processo pai e todos os seus filhos.

    Args:
        process (subprocess.Popen): Objeto do processo a ser encerrado.
    """
    try:
        # Envia um sinal SIGTERM para o grupo de processos
        try:
            log.write("yellow", "gracefully shutdown")
            process.terminate()
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            log.write("yellow", "force shutdown")
            process.kill()

    except ProcessLookupError:
        # O processo já foi encerrado
        pass

def kill_process(pid: int) -> None:
    """
    Encerra o processo identificado por `pid` de forma graciosa.

    Primeiro, envia SIGTERM para solicitar o encerramento.
    Em seguida, aguarda até 5 segundos verificando se o processo já encerrou.
    Se o processo ainda estiver ativo após esse período, envia SIGKILL para forçar o encerramento.

    Args:
        pid (int): O identificador do processo a ser encerrado.
    """
    try:
        # Envia o sinal SIGTERM para encerrar o processo graciosamente
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        return

    # Aguarda até 5 segundos, verificando se o processo encerrou
    timeout = 5.0
    interval = 0.1
    elapsed = 0.0
    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval
        try:
            # O sinal 0 não envia nenhum sinal real; ele verifica se o processo existe
            os.kill(pid, 0)
        except OSError:
            # Se ocorrer exceção, o processo já foi encerrado
            print(f"Processo {pid} encerrado graciosamente.")
            return

    # Se o processo ainda estiver ativo após 5 segundos, força o encerramento com SIGKILL
    try:
        os.kill(pid, signal.SIGKILL)
        print(f"Processo {pid} não encerrou em {timeout} segundos. SIGKILL enviado para forçar o encerramento.")
    except OSError as e:
        print(f"Erro ao enviar SIGKILL para o processo {pid}: {e}")

from dataclasses import dataclass

@dataclass
class ActiveProcess:
    process: any # permite
    pid: int


import subprocess
import sys
from typing import Protocol

class ConsoleHandler(Protocol):
    def write(self, message: str):
        """Deve ser implementado para definir onde a saída será exibida."""
        pass



# Implementação padrão que imprime no terminal (stdout)
class StdOutHandler:
    def write(self, message: str):
        sys.stdout.write(message + "\n")
        sys.stdout.flush()


# Implementação padrão que imprime no terminal (stdout)
class NoHandler:
    def write(self, message: str):
        pass

import subprocess
import threading
import io

class ConsoleHandler:
    def write(self, line):
        # Implemente aqui o que você deseja fazer com a saída
        print(line)  # Exemplo: apenas imprime a linha

class NoHandler(ConsoleHandler):
    def write(self, line):
        pass  # Não faz nada

import subprocess
import io
import threading
import subprocess
import io
import threading
import subprocess
import io
import threading
import os



import asyncio
import os
import io
from typing import Callable, Awaitable



class FailTest(Exception):
    def __init__(self, title, log_message):
        self.title = title
        self.log_message = log_message

def run_script_and_get_pid(
    cmd: list[str],
    project_root: str,
    logger_coro: Callable[[str, str], Awaitable[None]]
) -> Popen[bytes]:
    """
    Executa um comando shell de forma assíncrona em um diretório específico,
    redireciona a saída para uma função logger assíncrona personalizada.

    Args:
        cmd (list[str]): Comando shell a ser executado (como lista de strings).
        project_root (str): Diretório onde o comando será executado.
        logger_coro (Callable): Corrotina que recebe (linha, tipo de stream).

    Returns:
        tuple: (asyncio.subprocess.Process)
    """

    output_stream = io.StringIO()
    expanded_path = os.path.expanduser(project_root)

    if not os.path.exists(expanded_path):
        raise Exception(f"file/path {expanded_path} not found")


    process = subprocess.Popen(
        cmd,
        cwd=expanded_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    def stream_output(stream, stream_type):
        while True:
            line = stream.readline()
            if not line:
                break
            text = line.decode().strip()
            logger_coro(text, stream_type)
            output_stream.write(f"[{stream_type}] {text}\n")

    # Cria tasks para capturar stdout e stderr em paralelo
    threading.Thread(target = stream_output, args=(process.stdout, "stdout"))
    threading.Thread(target=stream_output, args=(process.stderr, "stderr"))

    return process



def create_postgres_connection(host: str, database: str, user: str, password: str, port: int = 5432):
    """
    Cria e retorna uma conexão com o banco de dados PostgreSQL.

    Parâmetros:
        host (str): Endereço do servidor PostgreSQL.
        database (str): Nome do banco de dados.
        user (str): Nome do usuário.
        password (str): Senha do usuário.
        port (int): Porta do servidor (padrão 5432).

    Retorna:
        connection: Objeto de conexão do psycopg2 que pode ser usado para executar queries.

    Lança:
        OperationalError: Caso haja problemas na conexão.
    """
    try:
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        print("Conexão com o PostgreSQL estabelecida com sucesso!")
        return connection
    except OperationalError as e:
        print(f"Erro ao conectar com o PostgreSQL: {e}")
        raise


# Exemplo de uso:
if __name__ == "__main__":
    conn = create_postgres_connection(
        host="localhost",
        database="meu_banco",
        user="admin",
        password="admin",
        port=12432,
    )
    # Utilize o objeto `conn` para criar um cursor e executar queries, por exemplo:
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
    cursor.close()
    conn.close()
