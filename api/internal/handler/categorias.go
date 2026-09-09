package handler

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/services"
)

type CategoriaLister interface {
	ListCategorias(context.Context) ([]domain.Categoria, error)
}

type CategoriasHandler struct {
	lister  CategoriaLister
	timeout time.Duration
}

type categoriasResponse struct {
	Meta totalItemsMeta      `json:"meta"`
	Data []categoriaResponse `json:"data"`
}

type categoriaResponse struct {
	Codigo string `json:"codigo"`
	Nome   string `json:"nome"`
}

func NewCategoriasHandler(lister CategoriaLister, timeout time.Duration) *CategoriasHandler {
	return &CategoriasHandler{
		lister:  lister,
		timeout: timeout,
	}
}

func (handler *CategoriasHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
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

	categorias, err := handler.lister.ListCategorias(ctx)
	if err != nil {
		if errors.Is(err, services.ErrDataNotReady) {
			WriteError(
				w,
				r,
				http.StatusServiceUnavailable,
				"DATA_NOT_READY",
				"categoria catalog unavailable",
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

	data := make([]categoriaResponse, len(categorias))
	for index, categoria := range categorias {
		data[index] = categoriaResponse{
			Codigo: categoria.Codigo,
			Nome:   categoria.Nome,
		}
	}

	WriteJSON(w, http.StatusOK, categoriasResponse{
		Meta: totalItemsMeta{TotalItems: len(data)},
		Data: data,
	})
}
