package factory

import "encoding/json"

func GetJsonFromBytes[T any](rawData []byte) (*T, error) {
	var dataParsed T
	err := json.Unmarshal(rawData, &dataParsed)
	if err != nil {
		return nil, err
	}

	return &dataParsed, nil
}
