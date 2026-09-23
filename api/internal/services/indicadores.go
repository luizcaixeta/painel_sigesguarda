package services

import (
	"context"
	"errors"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
)

type IndicadorRepository interface {
	CurrentSocioeconomicBatch(context.Context) (domain.CurrentBatch, error)
	LatestAnnualYear(context.Context, string) (int32, error)
	ListIndicadores(context.Context) ([]domain.Indicador, error)
	FiltersExist(context.Context, []string, []string) (bool, bool, error)
	ListIndicadorValores(context.Context, string, domain.IndicadoresFilter) ([]domain.IndicadorValor, error)
}

type IndicadorService struct {
	repository IndicadorRepository
}

func NewIndicadorService(repository IndicadorRepository) *IndicadorService {
	return &IndicadorService{repository: repository}
}

func (service *IndicadorService) ListIndicadores(ctx context.Context) ([]domain.Indicador, error) {
	indicadores, err := service.repository.ListIndicadores(ctx)
	if err != nil {
		return nil, wrapRepositoryError("list indicadores", err)
	}
	if len(indicadores) != 6 {
		return nil, errs.New(errs.KindIndicadorCatalogNotReady)
	}
	return indicadores, nil
}

func (service *IndicadorService) ListIndicadorValores(
	ctx context.Context,
	filter domain.IndicadoresFilter,
) ([]domain.IndicadorValor, error) {
	batch, err := service.repository.CurrentSocioeconomicBatch(ctx)
	if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
		return nil, errs.New(errs.KindCurrentSocioeconomicGoldBatchNotReady)
	}
	if err != nil {
		return nil, wrapRepositoryError("get current socioeconomic batch", err)
	}

	bairrosExist, indicadoresExist, err := service.repository.FiltersExist(
		ctx,
		filter.BairroIDs,
		filter.Indicadores,
	)
	if err != nil {
		return nil, wrapRepositoryError("validate indicator filters", err)
	}
	if !bairrosExist {
		return nil, errs.New(errs.KindInvalidBairroFilter)
	}
	if !indicadoresExist {
		return nil, errs.New(errs.KindInvalidIndicadorFilter)
	}

	if len(filter.Anos) == 0 && filter.De == nil {
		latestYear, err := service.repository.LatestAnnualYear(ctx, batch.ID)
		if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
			return nil, errs.New(errs.KindCurrentSocioeconomicGoldBatchNotReady)
		}
		if err != nil {
			return nil, wrapRepositoryError("get latest socioeconomic year", err)
		}
		filter.Anos = []int32{latestYear}
	}

	items, err := service.repository.ListIndicadorValores(ctx, batch.ID, filter)
	if err != nil {
		return nil, wrapRepositoryError("list indicator values", err)
	}
	return items, nil
}
