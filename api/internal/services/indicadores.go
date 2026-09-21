package services

import (
	"context"
	"errors"
	"fmt"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
)

var ErrInvalidIndicadorFilter = errors.New("invalid indicador filter")

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
		return nil, fmt.Errorf("list indicadores: %w", err)
	}
	if len(indicadores) != 6 {
		return nil, ErrDataNotReady
	}
	return indicadores, nil
}

func (service *IndicadorService) ListIndicadorValores(
	ctx context.Context,
	filter domain.IndicadoresFilter,
) ([]domain.IndicadorValor, error) {
	batch, err := service.repository.CurrentSocioeconomicBatch(ctx)
	if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
		return nil, ErrDataNotReady
	}
	if err != nil {
		return nil, fmt.Errorf("get current socioeconomic batch: %w", err)
	}

	bairrosExist, indicadoresExist, err := service.repository.FiltersExist(
		ctx,
		filter.BairroIDs,
		filter.Indicadores,
	)
	if err != nil {
		return nil, fmt.Errorf("validate indicator filters: %w", err)
	}
	if !bairrosExist {
		return nil, ErrInvalidBairroFilter
	}
	if !indicadoresExist {
		return nil, ErrInvalidIndicadorFilter
	}

	if len(filter.Anos) == 0 && filter.De == nil {
		latestYear, err := service.repository.LatestAnnualYear(ctx, batch.ID)
		if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
			return nil, ErrDataNotReady
		}
		if err != nil {
			return nil, fmt.Errorf("get latest socioeconomic year: %w", err)
		}
		filter.Anos = []int32{latestYear}
	}

	items, err := service.repository.ListIndicadorValores(ctx, batch.ID, filter)
	if err != nil {
		return nil, fmt.Errorf("list indicator values: %w", err)
	}
	return items, nil
}
