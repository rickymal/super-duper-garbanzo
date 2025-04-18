package facade

import (
	"context"
	"time"
)

// Facade pattern template

type AmqpContext[T any] struct {
	context.Context
	data T
}

func (amc *AmqpContext[T]) Deadline() (deadline time.Time, ok bool) {
	return amc.Deadline()
}

func (amc *AmqpContext[T]) Done() <-chan struct{} {
	return amc.Done()
}

func (amc *AmqpContext[T]) Err() error {
	return amc.Err()
}

func (amc *AmqpContext[T]) Value(key any) any {
	return amc.Value(key)
}
