package usecase

import (
	"context"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
	"ml-mq-auto/etc/ports"
)

type AuditoryLogService struct {
	logName string
}

func (a AuditoryLogService) OnDataReceived(messageContent rabbitAmqpPackage.Delivery) error {
	//TODO implement me
	panic("implement me")
}

func (a AuditoryLogService) OnErrorOccurs(err error) {
	//TODO implement me
	panic("implement me")
}

func (a AuditoryLogService) OnSuccess() {
	//TODO implement me
	panic("implement me")
}

func (a AuditoryLogService) WithContext(ctx context.Context) {
	//TODO implement me
	panic("implement me")
}

func WithAuditoryLog(s string) ports.IMessageHandler {
	var audt AuditoryLogService
	audt.logName = s
	return &audt
}
