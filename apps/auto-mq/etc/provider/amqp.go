package provider

import (
	rabbitAmqpPackage "github.com/rabbitmq/amqp091-go"
)

type AmpqConnectionFactory struct {
	conn *rabbitAmqpPackage.Connection
	Url  string
}

func (a AmpqConnectionFactory) GetRabbitMqConnection() (*rabbitAmqpPackage.Connection, error) {
	//TODO implement me
	panic("implement me")
}

func (a AmpqConnectionFactory) GetConsumer() (<-chan rabbitAmqpPackage.Delivery, error) {
	//TODO implement me
	panic("implement me")
}

func (a AmpqConnectionFactory) NewConnection(ch ConnectionHandler) (<-chan rabbitAmqpPackage.Delivery, error) {
	if a.conn == nil {
		conn, err := rabbitAmqpPackage.Dial(a.Url)
		if err != nil {
			return nil, err
		}
		a.conn = conn
	}

	channel, err := a.conn.Channel()
	if err != nil {
		return nil, err
	}

	for _, routingKey := range ch.RabbitRoutingKeys {
		var err error
		err = channel.QueueBind(
			ch.RabbitQueueName,
			routingKey,
			ch.RabbitExchangeName,
			ch.NoWait,
			ch.Args,
		)
		if err != nil {
			return nil, err
		}
	}

	msg, err := channel.Consume(
		ch.RabbitQueueName,
		"",
		ch.AutoAcknowledge,
		ch.Exclusive,
		ch.NoLocal,
		ch.NoWait,
		ch.Args,
	)
	if err != nil {
		return nil, err
	}

	return msg, nil

}
