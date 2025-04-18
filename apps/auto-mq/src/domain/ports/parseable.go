package ports

type IParseable interface {
	ToBytes() ([]byte, error)
}
