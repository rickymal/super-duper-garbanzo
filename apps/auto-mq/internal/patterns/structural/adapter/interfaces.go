package adapter

import (
	"context"
	amqp "github.com/rabbitmq/amqp091-go"
	"your_module_name/internal/patterns/structural/facade"
)

type IHandlerMessageBroker[T any] interface {
	CreateConnection(ctx context.Context, url string) error
	CreateChannel() (*amqp.Channel, error)
	Subscribe(ch *amqp.Channel, queueName string, routingKey []string, noWait bool, args amqp.Table, noLocal bool, exclusive bool, autoAck bool) (<-chan amqp.Delivery, error)
	InitConsumerObserver(ctx facade.AmqpContext[T], chn <-chan amqp.Delivery)
	OnDataReceived(bytes amqp.Delivery) (T, error)
	OnError(err error)
	OnSuccess(data T)
	GetConnection() error
}
