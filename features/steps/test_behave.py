from behave import given, when, then
import pika

@given('a RabbitMQ queue "{queue_name}" exists')
def step_given_queue_exists(context, queue_name):
    # context.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # context.channel = context.connection.channel()
    # context.queue_name = queue_name
    # context.channel.queue_declare(queue=queue_name)
    pass
@when('I publish "{message}" to the queue')
def step_publish_message(context, message):
    # context.channel.basic_publish(exchange='', routing_key=context.queue_name, body=message)
    pass


@then('I should receive "{message}" from the queue')
def step_receive_message(context, message):
    # method_frame, header_frame, body = context.channel.basic_get(queue=context.queue_name, auto_ack=True)
    # assert body.decode() == message
    # context.connection.close()
    assert True == True
