package entity

import "encoding/json"

// Buffer representes a array of bytes that wrappers a metodo for conversion names "ToStruct"
type Buffer[T any] []byte

// JSON2Struct make a parsing from json to struct typed
func (bf *Buffer[T]) JSON2Struct() (*T, error) {
	var data T
	return &data, json.Unmarshal(*bf, &data)
}
