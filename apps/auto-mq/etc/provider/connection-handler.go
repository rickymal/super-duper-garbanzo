package provider

import rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"

type ConnectionHandler struct {
	RabbitQueueName    string
	RabbitRoutingKeys  []string
	RabbitExchangeName string
	Args               rabbitAmqpPackage.Table
	NoWait             bool
	AutoAcknowledge    bool
	Exclusive          bool
	NoLocal            bool
}

func (h ConnectionHandler) Channel() (interface{}, interface{}) {

}
