package main

import (
	"automq/src/application/service"
	"context"
	"github.com/labstack/gommon/log"
	amqp "github.com/rabbitmq/amqp091-go"
	"os"
	"os/signal"
	"syscall"
	"time"
)

type Handler struct {
	ctx context.Context
}

func (h *Handler) OnClose(ctx context.Context) {
	//TODO implement me
	panic("implement me")
}

func (h *Handler) OnDataReceived(messageContent *amqp.Delivery) error {
	//TODO implement me
	log.Info("data received: ", string(messageContent.Body))
	return nil
}

func (h *Handler) OnSuccess() {
	log.Info("Opa deu certo patrão")
}

func (h *Handler) OnInit(ctx context.Context) {
	h.ctx = ctx
}

type IParseable interface {
	ToBytes() ([]byte, error)
}

type Data struct {
	Info string
}

func (Data) ToBytes() ([]byte, error) {
	return []byte("ola patrão"), nil
}

func main() {
	applicationContext, clcfnc := context.WithCancel(context.Background())
	var errCh chan error
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)
	amqpConnection, err := service.NewAmqpConnectionFactory(applicationContext, "amqp://guest:guest@localhost:5672", 2*time.Second)
	if err != nil {
		log.Fatal(err)
	}

	var mh Handler

	errCh = amqpConnection.NewConsumerFromUseCase(applicationContext, &mh, "loki")
	var data Data

	producer, _ := amqpConnection.NewProducer("loki")
	err = producer.Publish(data)
	if err != nil {
		log.Errorf("producer publish erro %v", err)
		return
	}

	select {
	case tp := <-sigChan:
		clcfnc()
		log.Fatal("signal happened. ", tp)
	case err := <-errCh:
		clcfnc()
		log.Fatal(err)
	case <-applicationContext.Done():
		log.Info("application context done")
	}

}
