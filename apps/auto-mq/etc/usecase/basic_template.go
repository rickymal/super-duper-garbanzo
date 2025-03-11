package usecase

import (
	"context"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
	"ml-mq-auto/etc/ports"
)

type MoveDataService struct {
	ctx context.Context
}

func ExtractData() ports.IMessageHandler {

}

type AnonymusHandler struct {
	onDataReceived func(data []byte) error
}

func (f *AnonymusHandler) OnDataReceived(messageContent rabbitAmqpPackage.Delivery) error {
	//TODO implement me
	panic("implement me")
}

func (f *AnonymusHandler) OnErrorOccurs(err error) {
	//TODO implement me
	panic("implement me")
}

func (f *AnonymusHandler) OnSuccess() {
	//TODO implement me
	panic("implement me")
}

func (f *AnonymusHandler) WithContext(ctx context.Context) {
	//TODO implement me
	panic("implement me")
}
