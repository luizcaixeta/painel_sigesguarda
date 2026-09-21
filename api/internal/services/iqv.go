package services

import (
	"context"
	"errors"
	"fmt"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
)

type IQVRepository interface {
	CurrentSocioeconomicBatch(context.Context) (domain.CurrentBatch, error)
	LatestAnnualYear(context.Context, string) (int32, error)
	FiltersExist(context.Context, []string, []string) (bool, bool, error)
	ListIQV(context.Context, string, domain.IQVFilter) ([]domain.IQV, error)
}

type IQVService struct {
	repository IQVRepository
}

func NewIQVService(repository IQVRepository) *IQVService {
	return &IQVService{repository: repository}
}

func (service *IQVService) ListIQV(
	ctx context.Context,
	filter domain.IQVFilter,
) ([]domain.IQV, error) {
	batch, err := service.repository.CurrentSocioeconomicBatch(ctx)
	if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
		return nil, ErrDataNotReady
	}
	if err != nil {
		return nil, fmt.Errorf("get current socioeconomic batch: %w", err)
	}

	bairrosExist, _, err := service.repository.FiltersExist(ctx, filter.BairroIDs, nil)
	if err != nil {
		return nil, fmt.Errorf("validate IQV filters: %w", err)
	}
	if !bairrosExist {
		return nil, ErrInvalidBairroFilter
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

	items, err := service.repository.ListIQV(ctx, batch.ID, filter)
	if err != nil {
		return nil, fmt.Errorf("list IQV: %w", err)
	}
	return items, nil
}
