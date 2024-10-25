Feature: Testar a integração com RabbitMQ

  Scenario: Publicar e consumir uma mensagem na fila
    Given a RabbitMQ queue "test_queue" exists
    When I publish "Hello RabbitMQ" to the queue
    Then I should receive "Hello RabbitMQ" from the queue

