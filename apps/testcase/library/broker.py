import pika
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote

def clear_all_queues(
    host: str = "localhost",
    port: int = 5672,
    username: str = "guest",
    password: str = "guest",
    virtual_host: str = "/",
    management_port: int = 15672,
):
    """
    Limpa todas as filas do RabbitMQ.
    :param virtual_host: Use "/" para o default ou outro vhost (codificado automaticamente).
    """
    connection = None
    try:
        # 1. Listar filas via API (tratando virtual host codificado)
        url = f"http://{host}:{management_port}/api/queues/{quote(virtual_host, safe='')}"
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()  # Lança erro se HTTP != 200
        queues = [q["name"] for q in response.json()]

        if not queues:
            print("Nenhuma fila encontrada.")
            return

        # 2. Conectar via AMQP e limpar filas
        credentials = pika.PlainCredentials(username, password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=virtual_host,
                credentials=credentials,
            )
        )
        channel = connection.channel()

        for queue_name in queues:
            channel.queue_purge(queue=queue_name)
            print(f"✅ Fila '{queue_name}' limpa.")

        print("🎉 Todas as filas foram limpas!")

    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro na API de gerenciamento: {e}\nVerifique: vhost, usuário/senha, ou plugin 'rabbitmq_management'.")
    except pika.exceptions.AMQPError as e:
        print(f"❌ Erro no AMQP: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        if connection and not connection.is_closed:
            connection.close()
import pika
from typing import Optional, Dict, Any


# Exemplo de uso
if __name__ == "__main__":
    clear_all_queues()

    import pika
    from typing import Optional, Dict, Any


class Broker:
    def __init__(
            self,
            exchange: str,
            routing_key: str,
            queue: str,
            host: str = 'localhost',
            exchange_type: str = 'direct',
            queue_args: Optional[dict[str, any]] = None,
    ):
        """
        Inicializa o Broker com os parâmetros necessários para conexão com o RabbitMQ.

        Args:
            exchange (str): Nome do exchange.
            routing_key (str): Chave de roteamento para publicação.
            queue (str): Nome da fila.
            host (str): Endereço do servidor RabbitMQ (padrão: 'localhost').
            exchange_type (str): Tipo do exchange (padrão: 'direct').
            queue_args (Optional[Dict[str, Any]]): Argumentos opcionais para a declaração da fila.
        """
        self.exchange = exchange
        self.routing_key = routing_key
        self.queue = queue
        self.host = host
        self.exchange_type = exchange_type
        self.queue_args = queue_args if queue_args else {}
        self.consumer_buffer = []  # ‘Buffer’ interno para armazenar mensagens consumidas

        # Cria a conexão e o canal com o RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()

        # Declara o exchange somente se ele não existir
        self._declare_exchange()

        # Declara a fila somente se ela não existir
        self._declare_queue()

        # Realiza o binding entre a fila e o exchange
        self._bind_queue()

    def _declare_exchange(self):
        """Declara o exchange somente se ele não existir."""
        try:
            # Tenta declarar o exchange de forma passiva (sem criar, apenas verificando)
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type=self.exchange_type,
                passive=True,  # Modo passivo: verifica se o exchange existe
                durable=True,
            )
        except pika.exceptions.ChannelClosedByBroker as e:
            if "NOT_FOUND" in str(e):
                # Se o exchange não existir, declara-o
                self.channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type=self.exchange_type,
                    durable=True,
                )
            else:
                raise e

    def _declare_queue(self):
        """Declara a fila somente se ela não existir."""
        try:
            # Tenta declarar a fila de forma passiva (sem criar, apenas verificando)
            self.channel.queue_declare(
                queue=self.queue,
                passive=True,  # Modo passivo: verifica se a fila existe
            )
        except pika.exceptions.ChannelClosedByBroker as e:
            if "NOT_FOUND" in str(e):
                # Se a fila não existir, declara-a com os argumentos fornecidos
                self.channel.queue_declare(
                    queue=self.queue,
                    durable=True,
                    arguments=self.queue_args,
                )
            else:
                raise e

    def _bind_queue(self):
        """Realiza o binding entre a fila e o exchange."""
        try:
            # Verifica se o binding já existe
            self.channel.queue_bind(
                queue=self.queue,
                exchange=self.exchange,
                routing_key=self.routing_key,
            )
        except pika.exceptions.ChannelClosedByBroker as e:
            if "NOT_FOUND" in str(e):
                # Se o binding não existir, cria-o
                self.channel.queue_bind(
                    queue=self.queue,
                    exchange=self.exchange,
                    routing_key=self.routing_key,
                )
            else:
                raise e

    def close(self):
        """Fecha a conexão com o RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


    def publish(self, message: str):
        """
        Publica uma mensagem no exchange utilizando a routing_key configurada.

        Args:
            message (str): A mensagem a ser publicada.
        """
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # Garante que a mensagem seja persistente
        )

    def consume(self, count: int) -> list[str]:
        """
        Consome até 'count' mensagens de forma não bloqueante, utilizando o buffer interno.

        Args:
            count (int): Número máximo de mensagens que se deseja consumir.

        Returns:
            list: Uma lista com as mensagens consumidas (como strings). Se não houver
                  mensagens suficientes, retorna todas as mensagens disponíveis.
        """
        messages = []

        # Primeiro, utiliza as mensagens que eventualmente já estejam no buffer
        while self.consumer_buffer and len(messages) < count:
            messages.append(self.consumer_buffer.pop(0))

        # Em seguida, realiza chamadas não bloqueantes para buscar mais mensagens, se necessário.
        while len(messages) < count:
            # Usa basic_get com auto_ack=False para buscar mensagens de forma não bloqueante
            method_frame, properties, body = self.channel.basic_get(queue=self.queue, auto_ack=False)
            if method_frame:
                # Converte o body para string (caso seja bytes)
                msg = body.decode() if isinstance(body, bytes) else body
                messages.append(msg)
                # Confirma (ack) o recebimento da mensagem
                self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            else:
                # Se a fila estiver vazia, encerra o loop
                break

        return messages


    def close(self):
        """
        Encerra a conexão com o RabbitMQ.
        """
        self.connection.close()
