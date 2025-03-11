import os
import signal
import time
import psycopg2
from psycopg2 import OperationalError

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
import logging
from typing import Protocol
import log

class ConsoleHandler(Protocol):
    def write(self, message: str):
        """Deve ser implementado para definir onde a saída será exibida."""
        log.logger.info(message)
        pass



# Implementação padrão que imprime no terminal (stdout)
class StdOutHandler:
    def write(self, message: str):
        sys.stdout.write(message + "\n")
        sys.stdout.flush()



# Função que executa o script e encaminha a saída para o handler desejado
def run_script_and_get_pid(script_path: str, console_handler: ConsoleHandler = StdOutHandler()):
    """
    Executa um script shell indicado por 'script_path' de forma assíncrona
    e redireciona a saída para um console_handler personalizado.

    Args:
        script_path (str): Caminho do script shell a ser executado.
        console_handler (ConsoleHandler): Objeto que processa a saída.

    Returns:
        subprocess.Popen: Objeto do processo rodando em segundo plano.
    """
    try:
        # Inicia o processo sem bloquear e captura stdout/stderr
        process = subprocess.Popen(
            script_path,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        logging.info(f"Processo iniciado com PID: {process.pid}")

        # Lendo a saída do processo linha por linha e enviando para o console_handler
        def stream_output(stream):
            for line in iter(stream.readline, ''):
                console_handler.write(line.strip())

        # Cria threads para não bloquear a aplicação enquanto lê a saída
        import threading
        threading.Thread(target=stream_output, args=(process.stdout,), daemon=True).start()
        threading.Thread(target=stream_output, args=(process.stderr,), daemon=True).start()

        # Retorna imediatamente o objeto do processo para controle externo
        return process

    except subprocess.SubprocessError as e:
        raise


# Exemplo de uso
if __name__ == "__main__":
    script_path = "./meu_script.sh"  # Substitua pelo caminho correto do script

    # Escolha o handler de saída
    console_handler = StdOutHandler()  # Saída normal no terminal
    # console_handler = RichConsoleHandler()  # Saída bonita com Rich (se instalado)

    process = run_script_and_get_pid(script_path, console_handler)

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
