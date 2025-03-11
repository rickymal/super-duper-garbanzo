package provider

type Consumer struct {
	Queue      string
	Exchange   string
	RoutingKey string
}

type JsonConsumerConfig struct {
	queue string
}

type WorkerManager struct{}

type HandleableEvent interface {
}

type BrokerConfig interface {
}

func (wm *WorkerManager) AddListener(handler HandleableEvent, brk BrokerConfig)

func (jcc *JsonConsumerConfig) onDataReceived(data []byte) {

}

func NewConsumer(queue string) *JsonConsumerConfig {
	return &JsonConsumerConfig{queue}
}

type MessageQueue[T any] struct {
	signal   uint
	service  string
	err      error
	metadata T
}
