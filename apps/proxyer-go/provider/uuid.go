package provider

import (
	"crypto/sha1"
	"encoding/json"
	"github.com/google/uuid"
)

func UUIDFromStruct(v any) (uuid.UUID, error) {
	b, err := json.Marshal(v)
	if err != nil {
		return uuid.Nil, err
	}
	namespace := uuid.MustParse("6ba7b810-9dad-11d1-80b4-00c04fd430c8") // ou defina seu próprio namespace
	return uuid.NewHash(sha1.New(), namespace, b, 5), nil
}
