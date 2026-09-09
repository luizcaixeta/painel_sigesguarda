package domain

import "encoding/json"

type Bairro struct {
	ID   string
	Nome string
}

type BairroGeometry struct {
	ID       string
	Nome     string
	Geometry json.RawMessage
}
