package handler

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
)

type IndicadorLister interface {
	ListIndicadores(context.Context) ([]domain.Indicador, error)
	ListIndicadorValores(context.Context, domain.IndicadoresFilter) ([]domain.IndicadorValor, error)
}

type IndicadoresCatalogoHandler struct {
	lister  IndicadorLister
	timeout time.Duration
}

type IndicadoresHandler struct {
	lister  IndicadorLister
	timeout time.Duration
}

type indicadoresCatalogoResponse struct {
	Meta totalItemsMeta      `json:"meta"`
	Data []indicadorResponse `json:"data"`
}

type indicadorResponse struct {
	Codigo  string `json:"codigo"`
	Nome    string `json:"nome"`
	Unidade string `json:"unidade"`
}

type indicadoresResponse struct {
	Meta totalItemsMeta           `json:"meta"`
	Data []indicadorValorResponse `json:"data"`
}

type indicadorValorResponse struct {
	BairroID       string  `json:"bairro_id"`
	Indicador      string  `json:"indicador"`
	Ano            int32   `json:"ano"`
	Valor          float64 `json:"valor"`
	TipoEstimativa string  `json:"tipo_estimativa"`
}

func NewIndicadoresCatalogoHandler(
	lister IndicadorLister,
	timeout time.Duration,
) *IndicadoresCatalogoHandler {
	return &IndicadoresCatalogoHandler{lister: lister, timeout: timeout}
}

func NewIndicadoresHandler(lister IndicadorLister, timeout time.Duration) *IndicadoresHandler {
	return &IndicadoresHandler{lister: lister, timeout: timeout}
}

func (handler *IndicadoresCatalogoHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if len(r.URL.Query()) != 0 {
		WriteError(w, r, errs.New(errs.KindInvalidArgument))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()
	indicadores, err := handler.lister.ListIndicadores(ctx)
	if err != nil {
		WriteError(w, r, err)
		return
	}

	data := make([]indicadorResponse, len(indicadores))
	for index, indicador := range indicadores {
		data[index] = indicadorResponse{
			Codigo:  indicador.Codigo,
			Nome:    indicador.Nome,
			Unidade: indicador.Unidade,
		}
	}
	WriteJSON(w, http.StatusOK, indicadoresCatalogoResponse{
		Meta: totalItemsMeta{TotalItems: len(data)},
		Data: data,
	})
}

func (handler *IndicadoresHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	filter, err := parseIndicadoresQuery(r.URL.Query())
	if err != nil {
		WriteError(w, r, errs.Wrap(errs.KindInvalidArgument, "parse indicadores query", err))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()
	items, err := handler.lister.ListIndicadorValores(ctx, filter)
	if err != nil {
		WriteError(w, r, err)
		return
	}

	data := make([]indicadorValorResponse, len(items))
	for index, item := range items {
		data[index] = indicadorValorResponse{
			BairroID:       item.BairroID,
			Indicador:      item.Indicador,
			Ano:            item.Ano,
			Valor:          item.Valor,
			TipoEstimativa: item.TipoEstimativa,
		}
	}
	WriteJSON(w, http.StatusOK, indicadoresResponse{
		Meta: totalItemsMeta{TotalItems: len(data)},
		Data: data,
	})
}

func parseIndicadoresQuery(query url.Values) (domain.IndicadoresFilter, error) {
	allowed := map[string]struct{}{
		"bairro_id": {}, "indicador": {}, "ano": {}, "de": {}, "ate": {},
	}
	for name := range query {
		if _, exists := allowed[name]; !exists {
			return domain.IndicadoresFilter{}, fmt.Errorf("unknown query parameter %q", name)
		}
	}

	annual, err := parseAnnualFilter(query)
	if err != nil {
		return domain.IndicadoresFilter{}, err
	}
	indicadores, err := parseUniqueValues(query, "indicador", 6)
	if err != nil {
		return domain.IndicadoresFilter{}, err
	}
	return domain.IndicadoresFilter{AnnualFilter: annual, Indicadores: indicadores}, nil
}
