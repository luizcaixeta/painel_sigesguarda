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

type IQVLister interface {
	ListIQV(context.Context, domain.IQVFilter) ([]domain.IQV, error)
}

type IQVHandler struct {
	lister  IQVLister
	timeout time.Duration
}

type iqvResponse struct {
	Meta totalItemsMeta    `json:"meta"`
	Data []iqvItemResponse `json:"data"`
}

type iqvItemResponse struct {
	BairroID       string  `json:"bairro_id"`
	Ano            int32   `json:"ano"`
	IQV            float64 `json:"iqv"`
	TipoEstimativa string  `json:"tipo_estimativa"`
}

func NewIQVHandler(lister IQVLister, timeout time.Duration) *IQVHandler {
	return &IQVHandler{lister: lister, timeout: timeout}
}

func (handler *IQVHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	filter, err := parseIQVQuery(r.URL.Query())
	if err != nil {
		WriteError(w, r, errs.Wrap(errs.KindInvalidArgument, "parse IQV query", err))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()
	items, err := handler.lister.ListIQV(ctx, filter)
	if err != nil {
		WriteError(w, r, err)
		return
	}

	data := make([]iqvItemResponse, len(items))
	for index, item := range items {
		data[index] = iqvItemResponse{
			BairroID:       item.BairroID,
			Ano:            item.Ano,
			IQV:            item.Valor,
			TipoEstimativa: item.TipoEstimativa,
		}
	}
	WriteJSON(w, http.StatusOK, iqvResponse{
		Meta: totalItemsMeta{TotalItems: len(data)},
		Data: data,
	})
}

func parseIQVQuery(query url.Values) (domain.IQVFilter, error) {
	allowed := map[string]struct{}{
		"bairro_id": {}, "ano": {}, "de": {}, "ate": {}, "ordem": {},
	}
	for name := range query {
		if _, exists := allowed[name]; !exists {
			return domain.IQVFilter{}, fmt.Errorf("unknown query parameter %q", name)
		}
	}

	annual, err := parseAnnualFilter(query)
	if err != nil {
		return domain.IQVFilter{}, err
	}
	order := "desc"
	if values, exists := query["ordem"]; exists {
		if len(values) != 1 || (values[0] != "asc" && values[0] != "desc") {
			return domain.IQVFilter{}, fmt.Errorf("invalid ordem")
		}
		order = values[0]
	}
	return domain.IQVFilter{AnnualFilter: annual, Ordem: order}, nil
}
