package usecase

import (
	"context"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
	"ml-mq-auto/etc/ports"
)

type WithPayloadService struct {
	ctx context.Context
}

func WithPayload() ports.IMessageHandler {
	var w WithPayloadService
	return &w
}

func (w WithPayloadService) OnDataReceived(messageContent rabbitAmqpPackage.Delivery) error {
	//type Payload struct {
	//	ClientKey string `json:"client_key"`
	//	Zone      string `json:"zone"`
	//}

	//var paylaod = factory.GetJsonFromBytes[Payload](messageContent.Body)

}

func (w WithPayloadService) OnErrorOccurs(err error) {

}

func (w WithPayloadService) OnSuccess() {

}

func (w WithPayloadService) WithContext(ctx context.Context) {
	w.ctx = ctx
}
