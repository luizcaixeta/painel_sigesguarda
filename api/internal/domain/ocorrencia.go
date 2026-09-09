package domain

import "time"

type Ocorrencia struct {
	BairroID   string
	Categoria  string
	Mes        time.Time
	Quantidade int32
}

type OcorrenciasFilter struct {
	BairroIDs  []string
	Categorias []string
	Meses      []time.Time
	De         *time.Time
	Ate        *time.Time
}

type CurrentBatch struct {
	ID          string
	DataThrough time.Time
}

type OcorrenciasResult struct {
	DataThrough time.Time
	Items       []Ocorrencia
}
