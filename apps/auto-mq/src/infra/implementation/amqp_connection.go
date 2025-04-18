package impl

import (
	"automq/src/domain/entity"
	ports "automq/src/domain/ports"
	"context"
	"github.com/labstack/gommon/log"
	rabbitAmqp "github.com/rabbitmq/amqp091-go"
	"time"
)

type amqpChannel struct {
	cancelChan    chan struct{}
	channelHealth chan struct{}
}

type AmqpConnection struct {
	amqpChannel
	ctx     context.Context
	conn    *rabbitAmqp.Connection
	channel *rabbitAmqp.Channel
	msgs    <-chan rabbitAmqp.Delivery
	queue   string
}

func NewAmqpConnection(ctx context.Context, conn *rabbitAmqp.Connection, channel *rabbitAmqp.Channel, queue string, config entity.AmqpConfig) (*AmqpConnection, error) {
	var amqpConnection = &AmqpConnection{ctx: ctx, conn: conn, channel: channel, queue: queue}

	if config.EnableConnectionCheck {
		go amqpConnection.enableConnectionCheck()
	}

	if config.EnableConsumingFromChannel {
		var err = amqpConnection.startConsuming(queue)
		if err != nil {
			return nil, err
		}
	}

	return amqpConnection, nil
}

func (ac *AmqpConnection) Publish(data ports.IParseable) error {
	bytes, err := data.ToBytes()
	if err != nil {
		return err
	}

	err = ac.channel.Confirm(false)
	if err != nil {
		log.Errorf("Error confirming channel %v", err)
		return err
	}

	var exchangeName = ac.queue + ".Exchange-fan"
	err = ac.channel.Publish(exchangeName, "", false, false, rabbitAmqp.Publishing{
		Headers:         nil,
		ContentType:     "application/json",
		ContentEncoding: "",
		DeliveryMode:    0,
		Priority:        0,
		CorrelationId:   "",
		ReplyTo:         "",
		Expiration:      "",
		MessageId:       "",
		Timestamp:       time.Now(),
		Type:            "",
		UserId:          "",
		AppId:           "",
		Body:            bytes,
	})
	if err != nil {
		log.Errorf("failed to publish message")
		return err
	}

	return nil
}

func (m *AmqpConnection) IsConnectionClosed() <-chan struct{} {
	return m.cancelChan
}

func (m *AmqpConnection) enableConnectionCheck() {

	m.channelHealth = nil
	var chn = make(chan struct{})
	m.channelHealth = chn
	defer close(m.channelHealth)

	closeChan := make(chan *rabbitAmqp.Error)
	m.conn.NotifyClose(closeChan)

	select {
	case err := <-closeChan:
		if err != nil {
			log.Warnf("Connection closed with error: %v", err)
		} else {
			log.Info("Connection closed gracefully")
		}
		m.channelHealth <- struct{}{} // Notifica o fechamento

	case <-m.ctx.Done():
		log.Info("Stopping connection health monitoring")
		return
	}
}

func (al *AmqpConnection) startConsuming(queueName string) error {
	var err error
	al.msgs, err = al.channel.Consume(
		queueName,
		"",    // consumer tag
		false, // auto-ack
		false, // exclusive
		false, // no-local
		false, // no-wait
		nil,   // args
	)
	return err
}

func (l *AmqpConnection) IsListenerCanceled() <-chan struct{} {
	return l.cancelChan
}

func (l *AmqpConnection) IsChannelClosed() <-chan struct{} {
	return l.cancelChan
}

func (l *AmqpConnection) GetNextMessage() <-chan rabbitAmqp.Delivery {
	return l.msgs
}

// CloseListener fecha o listener e libera recursos
func (l *AmqpConnection) CloseListener() error {
	close(l.cancelChan)
	if l.channel != nil {
		return l.channel.Close()
	}
	return nil
}

func (l *AmqpConnection) exchangeName() string {
	return l.queue + ".Exchange-dlx"
}
