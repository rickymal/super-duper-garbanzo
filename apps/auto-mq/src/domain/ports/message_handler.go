package ports

import (
	"context"
	amqp "github.com/rabbitmq/amqp091-go"
)

type IMessageHandler interface {
	OnDataReceived(messageContent *amqp.Delivery) error
	OnSuccess()
	OnInit(ctx context.Context)
	OnClose(ctx context.Context)
}
