package services

import (
	"context"
	"errors"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
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
		return nil, errs.New(errs.KindCurrentSocioeconomicGoldBatchNotReady)
	}
	if err != nil {
		return nil, wrapRepositoryError("get current socioeconomic batch", err)
	}

	bairrosExist, _, err := service.repository.FiltersExist(ctx, filter.BairroIDs, nil)
	if err != nil {
		return nil, wrapRepositoryError("validate IQV filters", err)
	}
	if !bairrosExist {
		return nil, errs.New(errs.KindInvalidBairroFilter)
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

	items, err := service.repository.ListIQV(ctx, batch.ID, filter)
	if err != nil {
		return nil, wrapRepositoryError("list IQV", err)
	}
	return items, nil
}
