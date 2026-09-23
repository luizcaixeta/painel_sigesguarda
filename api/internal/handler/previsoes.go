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

type PrevisaoLister interface {
	ListPrevisoes(
		context.Context,
		domain.PrevisoesFilter,
	) (domain.PrevisoesResult, error)
}

type PrevisoesHandler struct {
	lister  PrevisaoLister
	timeout time.Duration
}

type previsoesResponse struct {
	Meta previsoesMeta      `json:"meta"`
	Data []previsaoResponse `json:"data"`
}

type previsoesMeta struct {
	TotalItems    int    `json:"total_items"`
	ForecastRunID string `json:"forecast_run_id"`
	GoldBatchID   string `json:"gold_batch_id"`
	DataThrough   string `json:"data_through"`
	ModelName     string `json:"model_name"`
	ModelAlias    string `json:"model_alias"`
	MLflowRunID   string `json:"mlflow_run_id"`
	GeneratedAt   string `json:"generated_at"`
	ForecastMonth string `json:"forecast_month"`
}

type previsaoResponse struct {
	BairroID   string `json:"bairro_id"`
	Categoria  string `json:"categoria"`
	Mes        string `json:"mes"`
	Quantidade int32  `json:"quantidade"`
}

func NewPrevisoesHandler(lister PrevisaoLister, timeout time.Duration) *PrevisoesHandler {
	return &PrevisoesHandler{lister: lister, timeout: timeout}
}

func (handler *PrevisoesHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	filter, err := parsePrevisoesQuery(r.URL.Query())
	if err != nil {
		WriteError(w, r, errs.Wrap(errs.KindInvalidArgument, "parse previsoes query", err))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	result, err := handler.lister.ListPrevisoes(ctx, filter)
	if err != nil {
		WriteError(w, r, err)
		return
	}

	data := make([]previsaoResponse, len(result.Items))
	for index, item := range result.Items {
		data[index] = previsaoResponse{
			BairroID:   item.BairroID,
			Categoria:  item.Categoria,
			Mes:        item.Mes.Format("2006-01"),
			Quantidade: item.Quantidade,
		}
	}

	publication := result.Publication
	WriteJSON(w, http.StatusOK, previsoesResponse{
		Meta: previsoesMeta{
			TotalItems:    len(data),
			ForecastRunID: publication.RunID,
			GoldBatchID:   publication.GoldBatchID,
			DataThrough:   publication.DataThrough.Format("2006-01"),
			ModelName:     publication.ModelName,
			ModelAlias:    publication.ModelAlias,
			MLflowRunID:   publication.MLflowRunID,
			GeneratedAt:   publication.GeneratedAt.UTC().Format(time.RFC3339),
			ForecastMonth: publication.ForecastMonth.Format("2006-01"),
		},
		Data: data,
	})
}

func parsePrevisoesQuery(query url.Values) (domain.PrevisoesFilter, error) {
	allowed := map[string]struct{}{
		"bairro_id": {},
		"categoria": {},
	}
	for name := range query {
		if _, exists := allowed[name]; !exists {
			return domain.PrevisoesFilter{}, fmt.Errorf(
				"unknown query parameter %q",
				name,
			)
		}
	}

	bairroIDs, err := parseUniqueValues(query, "bairro_id", 75)
	if err != nil {
		return domain.PrevisoesFilter{}, err
	}
	for _, bairroID := range bairroIDs {
		if len(bairroID) > 100 {
			return domain.PrevisoesFilter{}, fmt.Errorf("invalid bairro_id")
		}
	}

	categorias, err := parseUniqueValues(query, "categoria", 6)
	if err != nil {
		return domain.PrevisoesFilter{}, err
	}

	return domain.PrevisoesFilter{
		BairroIDs:  bairroIDs,
		Categorias: categorias,
	}, nil
}
