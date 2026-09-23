package handler

import (
	"context"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
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
		WriteError(w, r, errs.Wrap(errs.KindInvalidArgument, "parse ocorrencias query", err))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	result, err := handler.lister.ListOcorrencias(ctx, filter)
	if err != nil {
		WriteError(w, r, err)
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
