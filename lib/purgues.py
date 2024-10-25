import pika

# Configura a conexão com o RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Nome da fila que você deseja purgar
queue_name = 'minha_fila'

# Purga (limpa) a fila
channel.queue_purge(queue=queue_name)

print(f"Fila '{queue_name}' foi purgada.")

# Fecha a conexão
connection.close()


import pika

# Configura a conexão com o RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Nome da fila que você deseja apagar
queue_name = 'minha_fila'

# Apaga a fila
channel.queue_delete(queue=queue_name)

print(f"Fila '{queue_name}' foi apagada.")

# Fecha a conexão
connection.close()
