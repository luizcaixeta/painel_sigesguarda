package services

import (
	"context"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
)

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
		return nil, wrapRepositoryError("list bairros", err)
	}

	if len(bairros) != 75 {
		return nil, errs.New(errs.KindBairroCatalogNotReady)
	}

	return bairros, nil
}

func (service *BairroService) ListBairrosGeoJSON(ctx context.Context) ([]domain.BairroGeometry, error) {
	bairros, err := service.repository.ListBairrosGeoJSON(ctx)
	if err != nil {
		return nil, wrapRepositoryError("list bairro geometries", err)
	}

	if len(bairros) != 75 {
		return nil, errs.New(errs.KindBairroGeometryCatalogNotReady)
	}

	return bairros, nil
}
