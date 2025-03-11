package amqppool

import (
	"errors"
	"github.com/streadway/amqp"
)

// ChannelPool gerencia um conjunto de canais do AMQP.
type ChannelPool struct {
	pool chan *amqp.Channel
}

// NewChannelPool cria um novo pool com a quantidade especificada de canais.
func NewChannelPool(conn *amqp.Connection, poolSize int) (*ChannelPool, error) {
	pool := make(chan *amqp.Channel, poolSize)
	for i := 0; i < poolSize; i++ {
		ch, err := conn.Channel()
		if err != nil {
			return nil, err
		}
		pool <- ch
	}
	return &ChannelPool{pool: pool}, nil
}

// Get retira um canal do pool. Se nenhum canal estiver disponível, a operação bloqueará até que um seja liberado.
func (p *ChannelPool) Get() (*amqp.Channel, error) {
	ch, ok := <-p.pool
	if !ok {
		return nil, errors.New("pool fechado")
	}
	return ch, nil
}

// Release devolve o canal para o pool.
func (p *ChannelPool) Release(ch *amqp.Channel) {
	p.pool <- ch
}

// Close fecha o pool e todos os canais contidos nele.
func (p *ChannelPool) Close() {
	close(p.pool)
	for ch := range p.pool {
		ch.Close()
	}
}
