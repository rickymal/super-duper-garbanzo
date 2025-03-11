package automq

import (
	"context"
	"github.com/labstack/gommon/log"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
	"ml-mq-auto/etc/ports"
	provider2 "ml-mq-auto/etc/provider"
)

func NewConsumerFromUsecase(ctx context.Context, config provider2.AmpqConnectionFactory, conn provider2.ConnectionHandler, connDlq provider2.ConnectionHandler, handler ports.IMessageHandler) {

	_NewConsumerFromUsecase(ctx, config, conn, handler)

	_NewConsumerFromUsecase(ctx, config, connDlq, handler)

}

func _NewConsumerFromUsecase(ctx context.Context, config provider2.AmpqConnectionFactory, conn provider2.ConnectionHandler, handler ports.IMessageHandler) {
	var err error
	//defer closeConnection(conn)
	//defer getChannel(conn)

	chn, err := config.NewConnection(conn)
	if err != nil {
		panic(err)
	}

	consumerContext, clcfnc := context.WithCancel(ctx)
	defer clcfnc()

	handler.WithContext(consumerContext)

	for {
		select {
		case <-ctx.Done():
			return
		default:
			processData(<-chn, handler)
		}
	}

}

func processData(messageContent rabbitAmqpPackage.Delivery, handler ports.IMessageHandler) {
	var err = handler.OnDataReceived(messageContent)
	if err != nil {
		log.Error("failed to handle message: %v", err)
		handler.OnErrorOccurs(err)
		return
	}
	handler.OnSuccess()
}
