package domain

type Indicador struct {
	Codigo  string
	Nome    string
	Unidade string
}

type IndicadorValor struct {
	BairroID       string
	Indicador      string
	Ano            int32
	Valor          float64
	TipoEstimativa string
}

type IQV struct {
	BairroID       string
	Ano            int32
	Valor          float64
	TipoEstimativa string
}

type AnnualFilter struct {
	BairroIDs []string
	Anos      []int32
	De        *int32
	Ate       *int32
}

type IndicadoresFilter struct {
	AnnualFilter
	Indicadores []string
}

type IQVFilter struct {
	AnnualFilter
	Ordem string
}
