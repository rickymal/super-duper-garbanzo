package domain

import (
	"context"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
	"your_module_name/internal/patterns/structural/adapter"
	"your_module_name/internal/patterns/structural/facade"
)

func NewConsumerFromUsecase[T any](ctx context.Context, handler adapter.IHandlerMessageBroker[T], autoAck bool, exclusive bool, noLocal bool, args rabbitAmqpPackage.Table, noWait bool, routingKey []string, queueName string) {
	var err error
	var consumerContext facade.AmqpContext[T]
	var clcfnc context.CancelFunc
	consumerContext.Context, clcfnc = context.WithCancel(ctx)
	defer clcfnc()

	chn, err := handler.CreateChannel()
	if err != nil {
		panic(err)
	}

	amqlChannel, err := handler.Subscribe(chn, queueName, routingKey, noWait, args, noLocal, exclusive, autoAck)
	if err != nil {
		panic(err)
	}

	for {
		select {
		case <-ctx.Done():
			return
		default:
			var data T
			var err error
			data, err = handler.OnDataReceived(<-amqlChannel)
			if err != nil {
				handler.OnError(err)
				continue
			}
			handler.OnSuccess(data)
		}
	}

}
