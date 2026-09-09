package handler

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/services"
)

type BairroLister interface {
	ListBairros(context.Context) ([]domain.Bairro, error)
}

type BairrosHandler struct {
	lister  BairroLister
	timeout time.Duration
}

type bairrosResponse struct {
	Meta totalItemsMeta   `json:"meta"`
	Data []bairroResponse `json:"data"`
}

type totalItemsMeta struct {
	TotalItems int `json:"total_items"`
}

type bairroResponse struct {
	BairroID string `json:"bairro_id"`
	Nome     string `json:"nome"`
}

func NewBairrosHandler(lister BairroLister, timeout time.Duration) *BairrosHandler {
	return &BairrosHandler{
		lister:  lister,
		timeout: timeout,
	}
}

func (handler *BairrosHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if len(r.URL.Query()) != 0 {
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

	bairros, err := handler.lister.ListBairros(ctx)
	if err != nil {
		if errors.Is(err, services.ErrDataNotReady) {
			WriteError(
				w,
				r,
				http.StatusServiceUnavailable,
				"DATA_NOT_READY",
				"bairro catalog unavailable",
			)
			return
		}

		WriteError(
			w,
			r,
			http.StatusServiceUnavailable,
			"DATABASE_UNAVAILABLE",
			"database unavailable",
		)
		return
	}

	data := make([]bairroResponse, len(bairros))
	for index, bairro := range bairros {
		data[index] = bairroResponse{
			BairroID: bairro.ID,
			Nome:     bairro.Nome,
		}
	}

	WriteJSON(w, http.StatusOK, bairrosResponse{
		Meta: totalItemsMeta{TotalItems: len(data)},
		Data: data,
	})
}
