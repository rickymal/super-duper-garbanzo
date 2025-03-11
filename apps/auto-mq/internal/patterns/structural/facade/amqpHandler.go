package facade

import (
	"github.com/labstack/gommon/log"
	amqp "github.com/rabbitmq/amqp091-go"
)

type AmqpConfig struct {
	queueName    string
	exchangeName string
	routingKey   []string
	noWait       bool
	args         amqp.Table
	noLocal      bool
	exclusive    bool
	autoAck      bool
}

type AmqpHandlerFacade[T any] struct {
	Connection *amqp.Connection
	amqpConfig AmqpConfig
}

func (ahf AmqpHandlerFacade[T]) CreateChannel() (*amqp.Channel, error) {
	chann, err := ahf.Connection.Channel()
	if err != nil {
		log.Errorf("failed to open ahf channel: %v", err)
		return nil, err
	}
	return chann, nil
}

func (ahf AmqpHandlerFacade[T]) Setup() AmqpConfig {
	
}

func (ahf AmqpHandlerFacade[T]) Subscribe(ch *amqp.Channel) (<-chan amqp.Delivery, error) {
	log.Info("Subscribing to queue")
	for _, rk := range ahf.amqpConfig.routingKey {
		var err = ch.QueueBind(ahf.amqpConfig.queueName, rk, ahf.amqpConfig.exchangeName, ahf.amqpConfig.noWait, ahf.amqpConfig.args)
		if err != nil {
			log.Errorf("failed to bind queue: %v", err)
			return nil, err
		}
	}

	//msg, err := ch.Consume(queueName, "", true, false, false, noWait, args)
	msg, err := ch.Consume(queueName, "", autoAck, exclusive, noLocal, noWait, args)

	return msg, err

}

func (ahf AmqpHandlerFacade[T]) InitConsumerObserver(ctx AmqpContext[T], chn <-chan amqp.Delivery) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
			var data T
			var err error
			data, err = ahf.OnDataReceived(<-chn)
			if err != nil {
				ahf.OnError(err)
				continue
			}
			ahf.OnSuccess(data)
		}
	}
}

func (ahf AmqpHandlerFacade[T]) OnDataReceived(bytes amqp.Delivery) (T, error) {
	panic("method should be implemented")
}

func (ahf AmqpHandlerFacade[T]) OnError(err error) {
	log.Errorf("failed to handle message: %v", err)
}

func (ahf AmqpHandlerFacade[T]) OnSuccess(data T) {
	log.Error("success to handle message")
}
