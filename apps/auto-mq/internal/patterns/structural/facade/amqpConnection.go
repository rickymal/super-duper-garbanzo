package facade

import (
	"github.com/labstack/gommon/log"
	amqp "github.com/rabbitmq/amqp091-go"
)

func AmqpConnection(url string) *amqp.Connection {
	var err error
	conn, err := amqp.Dial(url)
	if err != nil {
		log.Errorf("failed to connect to RabbitMQ: %v", err)
		panic(err)
	}

	return conn
}
