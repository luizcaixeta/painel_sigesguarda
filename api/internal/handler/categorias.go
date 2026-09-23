package handler

import (
	"context"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
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
		WriteError(w, r, errs.New(errs.KindInvalidArgument))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	categorias, err := handler.lister.ListCategorias(ctx)
	if err != nil {
		WriteError(w, r, err)
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
