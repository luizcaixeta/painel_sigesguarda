package handler

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/services"
)

type OcorrenciaLister interface {
	ListOcorrencias(
		context.Context,
		domain.OcorrenciasFilter,
	) (domain.OcorrenciasResult, error)
}

type OcorrenciasHandler struct {
	lister  OcorrenciaLister
	timeout time.Duration
}

type ocorrenciasResponse struct {
	Meta ocorrenciasMeta      `json:"meta"`
	Data []ocorrenciaResponse `json:"data"`
}

type ocorrenciasMeta struct {
	DataThrough string `json:"data_through"`
	TotalItems  int    `json:"total_items"`
}

type ocorrenciaResponse struct {
	BairroID   string `json:"bairro_id"`
	Categoria  string `json:"categoria"`
	Mes        string `json:"mes"`
	Quantidade int32  `json:"quantidade"`
}

func NewOcorrenciasHandler(lister OcorrenciaLister, timeout time.Duration) *OcorrenciasHandler {
	return &OcorrenciasHandler{
		lister:  lister,
		timeout: timeout,
	}
}

func (handler *OcorrenciasHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	filter, err := parseOcorrenciasQuery(r.URL.Query())
	if err != nil {
		WriteError(
			w,
			r,
			http.StatusBadRequest,
			"INVALID_ARGUMENT",
			"invalid query parameter",
		)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	result, err := handler.lister.ListOcorrencias(ctx, filter)
	if err != nil {
		handler.writeError(w, r, err)
		return
	}

	data := make([]ocorrenciaResponse, len(result.Items))
	for index, ocorrencia := range result.Items {
		data[index] = ocorrenciaResponse{
			BairroID:   ocorrencia.BairroID,
			Categoria:  ocorrencia.Categoria,
			Mes:        ocorrencia.Mes.Format("2006-01"),
			Quantidade: ocorrencia.Quantidade,
		}
	}

	WriteJSON(w, http.StatusOK, ocorrenciasResponse{
		Meta: ocorrenciasMeta{
			DataThrough: result.DataThrough.Format("2006-01"),
			TotalItems:  len(data),
		},
		Data: data,
	})
}

func (handler *OcorrenciasHandler) writeError(w http.ResponseWriter, r *http.Request, err error) {
	switch {
	case errors.Is(err, services.ErrInvalidBairroFilter):
		WriteError(w, r, http.StatusBadRequest, "INVALID_FILTER", "unknown bairro_id")
	case errors.Is(err, services.ErrInvalidCategoriaFilter):
		WriteError(w, r, http.StatusBadRequest, "INVALID_FILTER", "unknown categoria")
	case errors.Is(err, services.ErrDataNotReady):
		WriteError(w, r, http.StatusServiceUnavailable, "DATA_NOT_READY", "current Gold batch unavailable")
	default:
		WriteError(w, r, http.StatusServiceUnavailable, "DATABASE_UNAVAILABLE", "database unavailable")
	}
}
