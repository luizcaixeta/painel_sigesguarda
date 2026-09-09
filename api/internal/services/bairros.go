package services

import (
	"context"
	"errors"
	"fmt"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

var ErrDataNotReady = errors.New("data not ready")

type BairroRepository interface {
	ListBairros(context.Context) ([]domain.Bairro, error)
	ListBairrosGeoJSON(context.Context) ([]domain.BairroGeometry, error)
}

type BairroService struct {
	repository BairroRepository
}

func NewBairroService(repository BairroRepository) *BairroService {
	return &BairroService{repository: repository}
}

func (service *BairroService) ListBairros(ctx context.Context) ([]domain.Bairro, error) {
	bairros, err := service.repository.ListBairros(ctx)
	if err != nil {
		return nil, fmt.Errorf("list bairros: %w", err)
	}

	if len(bairros) != 75 {
		return nil, ErrDataNotReady
	}

	return bairros, nil
}

func (service *BairroService) ListBairrosGeoJSON(ctx context.Context) ([]domain.BairroGeometry, error) {
	bairros, err := service.repository.ListBairrosGeoJSON(ctx)
	if err != nil {
		return nil, fmt.Errorf("list bairro geometries: %w", err)
	}

	if len(bairros) != 75 {
		return nil, ErrDataNotReady
	}

	return bairros, nil
}
