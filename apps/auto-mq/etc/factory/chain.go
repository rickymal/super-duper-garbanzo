package factory

import (
	"context"
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
	"ml-mq-auto/etc/ports"
)

// WithMiddlewares recebe um handler base e um conjunto de middlewares (ou encadeáveis)
// e os encadeia de modo que o primeiro da lista seja o mais externo.
// A função aplica os encadeamentos em ordem reversa.
func WithMiddlewares(base ports.IMessageHandler, chain ...func(data ports.IMessageHandler) ports.IMessageHandler) ports.IMessageHandler {
	final := base
	// Encadeia de trás para frente para que o primeiro middleware seja o mais externo.
	for i := len(chain) - 1; i >= 0; i-- {
		final = chain[i](final)
	}
	return final
}

// WithMiddlewares recebe um handler base e um conjunto de middlewares (ou encadeáveis)
// e os encadeia de modo que o primeiro da lista seja o mais externo.
// A função aplica os encadeamentos em ordem reversa.

type MiddlwareUsecase struct {
	chain             []ports.IMessageHandler
	actualStep        ports.IMessageHandler
	middlewareContext context.Context
}

func (m MiddlwareUsecase) OnDataReceived(messageContent rabbitAmqpPackage.Delivery) error {
	for _, handler := range m.chain {
		m.actualStep = handler
		var err = m.OnDataReceived(messageContent)
		if err != nil {
			return err
		}
	}

	return nil
}

func (m MiddlwareUsecase) OnErrorOccurs(err error) {
	m.actualStep.OnErrorOccurs(err)
}

func (m MiddlwareUsecase) OnSuccess() {
	m.actualStep.OnSuccess()
}

func (m MiddlwareUsecase) WithContext(ctx context.Context) {
	m.middlewareContext = context.WithoutCancel(ctx)
}

func MiddlewareFromUsecase(chain ...ports.IMessageHandler) ports.IMessageHandler {
	var middlewareUsecase MiddlwareUsecase
	middlewareUsecase.chain = chain
	return &middlewareUsecase
}
