package services

import (
	"context"
	"fmt"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
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
		return nil, fmt.Errorf("list categorias: %w", err)
	}

	if len(categorias) != 6 {
		return nil, ErrDataNotReady
	}

	return categorias, nil
}
