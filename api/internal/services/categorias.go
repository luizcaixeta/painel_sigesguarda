package services

import (
	"context"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
)

type CategoriaRepository interface {
	ListCategorias(context.Context) ([]domain.Categoria, error)
}

type CategoriaService struct {
	repository CategoriaRepository
}

func NewCategoriaService(repository CategoriaRepository) *CategoriaService {
	return &CategoriaService{repository: repository}
}

func (service *CategoriaService) ListCategorias(
	ctx context.Context,
) ([]domain.Categoria, error) {
	categorias, err := service.repository.ListCategorias(ctx)
	if err != nil {
		return nil, wrapRepositoryError("list categorias", err)
	}

	if len(categorias) != 6 {
		return nil, errs.New(errs.KindCategoriaCatalogNotReady)
	}

	return categorias, nil
}
