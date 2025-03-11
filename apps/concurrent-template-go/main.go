package main

import (
	"base/provider"
	"context"
	"fmt"
	"time"
)

type Handler1 struct {
	ctx context.Context
}

type Handler2 struct {
	ctx context.Context
}
type UsecaseManager struct {
	provider.Consumer
}

func (uc *Handler1) setup() {

}

func (uc *Handler1) run(data []byte) chan provider.MessageQueue {

}

func (uc *Handler1) onError(err error) {

}

type ContextManager struct {
	context.Context
}

func main() int {
	// Env config
	env, err := provider.LoadEnvVariables()

	wm := provider.WorkerManager()

	wm.AddListener(new(Handler1), provider.NewConsumer("queue", env))
	wm.AddListener(new(Handler2), provider.NewConsumer("queue", env))

	if wm.Setup() != nil {
		panic("")
	}

	// Como criar uma função anônima que tem as funções necessárias e que dispara o signal do sistema operacional?
	wm.AddUseCase()

	rootContext, cancelFn := context.WithTimeout(context.Background(), 2*time.Hour)
	rootContext = wm.Run(rootContext)

	select {
	case <-rootContext.Done():
		fmt.Println("Root context canceled:", rootContext.Err()) // Lide com o erro
		return -1                                                // Ou outro valor indicando erro

	case <-wm.Wait():
		fmt.Println("Wait completed")
		return 0

	case event := <-wm.Event():
		switch event {
		case provider.ENUM_OS_SIGNAL:
			fmt.Println("Received OS signal")
			// Lógica adicional aqui
		default:
			fmt.Println("Unknown event:", event)
		}
	}

}
