package application

import (
	"context"
	"your_module_name/etc/ports"
	"your_module_name/internal/domain"
	"your_module_name/internal/patterns/structural/facade"
)

func RunEtl() {
	var appCtx = context.Background()

	amqpConnection := facade.AmqpConnection("OI")
	domain.NewConsumerFromUsecase(appCtx, facade.AmqpHandlerFacade[any]{Connection: amqpConnection})
	domain.NewConsumerFromUsecase(appCtx, facade.AmqpHandlerFacade[any]{Connection: amqpConnection})
	domain.NewConsumerFromUsecase(appCtx, facade.AmqpHandlerFacade[any]{Connection: amqpConnection})
}
