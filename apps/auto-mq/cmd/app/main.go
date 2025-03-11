package main

import (
	"context"
	"your_module_name/etc/automq"
	"your_module_name/etc/factory"
)

type MyHandler struct{}

func (mh *MyHandler) example(data string) error {

}

func do(data func(data string) error) {

}

func main() {
	var applicationContext = context.Background()

	var mh MyHandler
	do(mh.example)

	go automq.NewConsumerFromUsecase(
		applicationContext,
		provider2.AmpqConnectionFactory{
			Url: "amqp://guest:guest@localhost:5672/",
		},
		provider2.ConnectionHandler{
			RabbitQueueName:    "q1",
			RabbitRoutingKeys:  []string{"rk1"},
			RabbitExchangeName: "ex1",
			Args:               nil,
			NoWait:             false,
			AutoAcknowledge:    false,
			Exclusive:          false,
			NoLocal:            false,
		},
		provider2.ConnectionHandler{
			RabbitQueueName:    "q1-dlq",
			RabbitRoutingKeys:  []string{"rk1-dlq"},
			RabbitExchangeName: "ex1-dlx",
			Args:               nil,
			NoWait:             false,
			AutoAcknowledge:    false,
			Exclusive:          false,
			NoLocal:            false,
		},
		factory.MiddlewareFromUsecase(
			usecase2.WithPayload(),
			usecase2.WithAuditoryLog("step-1"),
			usecase2.ExtractData(),
		),
	)

}
