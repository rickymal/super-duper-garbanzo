package ports

import (
	"context"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
)

type IMessageHandler interface {
	OnDataReceived(messageContent rabbitAmqpPackage.Delivery) error
	OnErrorOccurs(err error)
	OnSuccess()
	WithContext(ctx context.Context)
}
