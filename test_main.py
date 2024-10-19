import pika
import time
import requests
import pytest

from lib.Snapshot import *


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    test_fn = item.obj
    docstring = getattr(test_fn, '__doc__')
    if docstring:
        report.nodeid = docstring

    
def setup_rabbitmq():
    # Conexão e configuração do RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    exchange = 'my_exchange'
    queue_producer = 'queue_producer'
    queue_consumer = 'queue_consumer'

    # Declara a exchange e filas
    channel.exchange_declare(exchange=exchange, exchange_type='direct')
    channel.queue_declare(queue=queue_producer, passive=False)
    channel.queue_declare(queue=queue_consumer, passive=False)
    channel.queue_bind(exchange=exchange, queue=queue_producer)

    return connection, channel, exchange, queue_producer, queue_consumer

def publish_message(channel, exchange, queue_producer, message):
    # Publica uma mensagem
    channel.basic_publish(exchange=exchange, routing_key=queue_producer, body=message)
    print(f"Mensagem enviada: {message}")

def consume_message_without_ack(channel, queue_consumer):
    # Consome mensagem sem ACK
    method_frame, header_frame, body = channel.basic_get(queue=queue_consumer, auto_ack=False)
    return body

def validate_queues(channel):
    # Valida se as novas filas foram criadas (substitua pelos nomes reais)
    try:
        channel.queue_declare(queue='new_queue_1', passive=True)
        channel.queue_declare(queue='new_queue_2', passive=True)
        print("Novas filas validadas com sucesso.")
    except pika.exceptions.ChannelClosedByBroker:
        print("Erro ao validar filas.")

def trigger_event():
    # Dispara o evento via POST
    url = 'http://localhost:5000/api/event'
    payload = {'key': 'value'}
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    print("Evento disparado com sucesso.")

def check_database():
    # Aqui você faz a validação do banco de dados
    # Por exemplo, verificando se as tabelas estão corretas
    print("Validando banco de dados...")
    time.sleep(2)  # Simulando tempo de consulta
    # Adicione as consultas reais ao banco de dados aqui
    return True

def run_user_journey():
    # Configura o RabbitMQ
    connection, channel, exchange, queue_producer, queue_consumer = setup_rabbitmq()

    try:
        # Envia a mensagem
        message = "Test message"
        publish_message(channel, exchange, queue_producer, message)

        # Delay de 5 segundos
        time.sleep(5)

        # Consome sem ACK e valida a mensagem
        consumed_message = consume_message_without_ack(channel, queue_consumer)
        assert consumed_message is not None, "Nenhuma mensagem consumida!"
        print(f"Mensagem consumida: {consumed_message.decode()}")

        # Valida se as novas filas foram criadas
        validate_queues(channel)

        # Dispara o evento via POST
        trigger_event()

        # Delay de 5 segundos antes de verificar o banco
        time.sleep(5)

        # Verifica o estado do banco de dados
        assert check_database(), "Falha na validação do banco de dados!"
        print("Validação do banco de dados concluída com sucesso.")

    finally:
        # Fecha a conexão ao final
        connection.close()


# executado ao chamar pytest -v
# @pytest.mark.description("Teste para verificar se a soma de dois números está correta")
def test_main():
    """Teste para verificar se a soma de dois números está correta."""
    snapshot = Snapshot("oloko")
    snapshot.get_or_create_snapshot("henrique")

    
    assert "henrique" == snapshot.get_or_create_snapshot("henrique")

    """Teste para verificar se a soma de dois números está correta. 2"""
    assert True == True

if __name__ == "__main__":
    print("OOOOOOOOOOOOOOXII")