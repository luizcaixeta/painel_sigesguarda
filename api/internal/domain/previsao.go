package domain

import "time"

type Previsao struct {
	BairroID   string
	Categoria  string
	Mes        time.Time
	Quantidade int32
}

type PrevisoesFilter struct {
	BairroIDs  []string
	Categorias []string
}

type ForecastPublication struct {
	RunID         string
	GoldBatchID   string
	DataThrough   time.Time
	ForecastMonth time.Time
	ModelName     string
	ModelAlias    string
	MLflowRunID   string
	GeneratedAt   time.Time
}

type PrevisoesResult struct {
	Publication ForecastPublication
	Items       []Previsao
}
