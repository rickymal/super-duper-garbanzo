package service

import (
	"automq/src/domain/entity"
	ports "automq/src/domain/ports"
	impl "automq/src/infra/implementation"
	"context"
	"errors"
	"fmt"
	"github.com/labstack/gommon/log"
	amqp "github.com/rabbitmq/amqp091-go"
	"sync"
	"time"
)

type AmqpConnectionFactory struct {
	ctx              context.Context
	actualConnection *amqp.Connection
	mu               sync.Mutex
	amqpUrl          string
	interval         time.Duration
}

// NewAmqpConnectionFactory cria um novo gerenciador de conexões (agora como função, não método)
func NewAmqpConnectionFactory(ctx context.Context, url string, interval time.Duration) (*AmqpConnectionFactory, error) {
	manager := &AmqpConnectionFactory{
		ctx:      ctx,
		amqpUrl:  url,
		interval: interval,
	}
	return manager, nil
}

func (mn *AmqpConnectionFactory) NewProducer(queueName string) (*impl.AmqpConnection, error) {
	amqpConnection, err := mn.newAmqpConnection(queueName, entity.AmqpConfig{
		EnableConnectionCheck:      false,
		SetupInfrastructure:        false,
		EnableConsumingFromChannel: false,
	})
	if err != nil {
		log.Errorf("Error creating AmqpConnection %v", err)
		return nil, err
	}

	return amqpConnection, nil
}

func (mn *AmqpConnectionFactory) NewConsumerFromUseCase(ctx context.Context, handler ports.IMessageHandler, queueName string) chan error {
	handler.OnInit(ctx)
	var errCh = make(chan error)
	go mn.startListener(errCh, queueName, ctx, handler)
	return errCh
}

func (mn *AmqpConnectionFactory) startListener(ch chan error, queueName string, ctx context.Context, handler ports.IMessageHandler) {
	defer handler.OnClose(ctx)
	for {
		select {
		case <-ctx.Done():
			log.Warnf("context canceled, connection closed")
			return
		default:
			// Configuração simplificada da conexão
			amqpConnection, err := mn.newAmqpConnection(queueName, entity.AmqpConfig{
				EnableConnectionCheck:      true,
				EnableConsumingFromChannel: true,
				SetupInfrastructure:        true,
			})
			if err != nil {
				log.Errorf("Error creating amqp connection: %s", err)
				if err := mn.Close(); err != nil {
					log.Error("Error closing amqp connection: ", err)
				}
				time.Sleep(mn.interval)
				continue
			}

			// Processamento de mensagens
			if err := processMessage(amqpConnection, handler, ctx); err != nil {
				log.Errorf("Message processing error: %v", err)
				time.Sleep(mn.interval)
			}
		}
	}
}

// Função separada para processamento de mensagens
func processMessage(conn *impl.AmqpConnection, handler ports.IMessageHandler, ctx context.Context) error {
	for {
		select {
		case <-conn.IsChannelClosed():
			return fmt.Errorf("channel closed")
		case <-conn.IsConnectionClosed():
			return fmt.Errorf("connection closed")
		case <-ctx.Done():
			return nil
		case msg, ok := <-conn.GetNextMessage():
			if !ok {
				return fmt.Errorf("message channel closed")
			}

			if err := handleSingleMessage(&msg, handler); err != nil {
				return err
			}
		}
	}
}

// Tratamento individual de mensagem
func handleSingleMessage(msg *amqp.Delivery, handler ports.IMessageHandler) error {
	hErr := handler.OnDataReceived(msg)

	switch {
	case hErr == nil:
		handler.OnSuccess()
		if err := msg.Ack(false); err != nil {
			log.Errorf("Error acking message: %v", err)
			return err
		}
	case errors.As(hErr, &amqp.Error{}):
		return hErr // Força reconexão
	default:
		if err := msg.Nack(false, false); err != nil {
			log.Errorf("Error nacking message: %v", err)
			return err
		}
	}
	return nil
}

func (mn *AmqpConnectionFactory) setupInfrastructure(queueName string) error {
	mn.mu.Lock()
	defer mn.mu.Unlock()

	var exchangeFanout = queueName + ".Exchange" + "-fan"
	var exchangeDeadLetter = queueName + ".Exchange" + "-dlx"
	var queueSnapshot = queueName + "-snap"
	var queueDeadLetter = queueName + "-dlq"

	channel, err := mn.actualConnection.Channel()
	if err != nil {
		return fmt.Errorf("failed to open channel: %w", err)
	}
	defer func(channel *amqp.Channel) {
		err := channel.Close()
		if err != nil {

		}
	}(channel)

	// Configura exchange principal
	err = channel.ExchangeDeclare(
		exchangeFanout,
		"fanout",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		return fmt.Errorf("failed to declare exchange: %w", err)
	}

	// configura DLX
	err = channel.ExchangeDeclare(
		exchangeDeadLetter,
		"topic",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		return fmt.Errorf("failed to declare DLX: %w", err)
	}

	// Configura fila principal
	_, err = channel.QueueDeclare(
		queueName,
		true,
		false,
		false,
		false,
		amqp.Table{
			"x-dead-letter-exchange":    exchangeDeadLetter,
			"x-dead-letter-routing-key": "final-dlq",
		},
	)
	if err != nil {
		log.Errorf("failed to declare retry queue %s: %v", queueName, err)
		return err
	}

	// Configura fila de snapshot
	_, err = channel.QueueDeclare(
		queueSnapshot,
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Errorf("failed to declare snapshot retry queue %s: %v", queueName, err)
		return err
	}

	err = channel.QueueBind(
		queueName,
		"",
		exchangeFanout,
		false,
		nil,
	)
	if err != nil {
		log.Errorf("failed to bind retry queue %s: %w", queueName, err)
		return err
	}

	err = channel.QueueBind(
		queueSnapshot,
		"",
		exchangeFanout,
		false,
		nil,
	)
	if err != nil {
		log.Errorf("failed to bind retry queue %s: %w", queueName, err)
		return err
	}

	// Configura DLQ
	_, err = channel.QueueDeclare(
		queueDeadLetter,
		true,
		false,
		false,
		false,
		amqp.Table{
			"x-headers-preserved":    true,
			"x-dead-letter-exchange": exchangeFanout,
			"x-message-ttl":          15000,
		},
	)
	if err != nil {
		log.Errorf("failed to declare DLQ: %v", err)
		return err
	}

	err = channel.QueueBind(
		queueDeadLetter,
		"final-dlq",
		exchangeDeadLetter,
		false,
		nil,
	)
	if err != nil {
		log.Errorf("failed to bind DLQ: %v", err)
		return err
	}

	return nil
}

// Close fecha todos os recursos
func (mn *AmqpConnectionFactory) Close() error {
	var err error
	mn.mu.Lock()
	defer mn.mu.Unlock()

	// Fechar conexão
	if mn.actualConnection != nil {
		if err = mn.actualConnection.Close(); err != nil {
			log.Warnf("Failed to close connection: %v", err)
		}
	}

	return err
}

func (mn *AmqpConnectionFactory) newAmqpConnection(queueName string, config entity.AmqpConfig) (*impl.AmqpConnection, error) {
	var err error
	if mn.actualConnection == nil || mn.actualConnection.IsClosed() {
		log.Infof("trying connect to amqp server: %v", mn.amqpUrl)
		mn.actualConnection, err = amqp.Dial(mn.amqpUrl)
		if err != nil {
			mn.actualConnection = nil
			return nil, fmt.Errorf("failed to connect to RabbitMQ: %w", err)
		}
	}
	log.Infof("connection stablished: %v", mn.amqpUrl)
	channelConsumer, err := mn.actualConnection.Channel()
	if err != nil {
		log.Fatal(err)
	}

	var amqpListener, errAmqp = impl.NewAmqpConnection(mn.ctx, mn.actualConnection, channelConsumer, queueName, config)
	if errAmqp != nil {
		log.Errorf("failed to open connection to RabbitMQ: %v", errAmqp)
		return nil, errAmqp
	}

	if config.SetupInfrastructure {
		err = mn.setupInfrastructure(queueName)
		if err != nil {
			return nil, err
		}
	}

	return amqpListener, nil
}
