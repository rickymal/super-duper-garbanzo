import pika


class Broker:
    def __init__(self, exchange: str, routing_key: str, queue: str, host: str = 'localhost'):
        """
        Inicializa o Broker com os parâmetros necessários para conexão com o RabbitMQ.

        Args:
            exchange (str): Nome do exchange.
            routing_key (str): Chave de roteamento para publicação.
            queue (str): Nome da fila.
            host (str): Endereço do servidor RabbitMQ (padrão: 'localhost').
        """
        self.exchange = exchange
        self.routing_key = routing_key
        self.queue = queue
        self.host = host
        self.consumer_buffer = []  # ‘Buffer’ interno para armazenar mensagens consumidas

        # Cria a conexão e o canal com o RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()

        # Declara o exchange, a fila e realiza o binding entre eles
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct', durable=True)
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.channel.queue_bind(queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)

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

    def consume(self, count: int):
        """
        Consome até 'count' mensagens de forma não bloqueante, utilizando o buffer interno.

        Args:
            count (int): Número de mensagens que se deseja consumir.

        Returns:
            list: Uma lista com as mensagens consumidas (como strings). Se não houver
                  mensagens suficientes, retorna o que estiver disponível.
        """
        messages = []

        # Primeiro, utiliza as mensagens que eventualmente já estejam no buffer
        while self.consumer_buffer and len(messages) < count:
            messages.append(self.consumer_buffer.pop(0))

        # Em seguida, realiza chamadas não bloqueantes para buscar mais mensagens, se necessário.
        while len(messages) < count:
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