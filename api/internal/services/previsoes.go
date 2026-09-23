package services

import (
	"context"
	"errors"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
)

type PrevisaoRepository interface {
	CurrentMLBatch(context.Context) (domain.CurrentBatch, error)
	FindCurrentPublication(
		context.Context,
		string,
		time.Time,
		time.Time,
	) (domain.ForecastPublication, error)
	FiltersExist(context.Context, []string, []string) (bool, bool, error)
	ListForecastItems(
		context.Context,
		domain.ForecastPublication,
		domain.PrevisoesFilter,
	) ([]domain.Previsao, error)
}

type PrevisaoService struct {
	repository PrevisaoRepository
}

func NewPrevisaoService(repository PrevisaoRepository) *PrevisaoService {
	return &PrevisaoService{repository: repository}
}

func (service *PrevisaoService) ListPrevisoes(
	ctx context.Context,
	filter domain.PrevisoesFilter,
) (domain.PrevisoesResult, error) {
	batch, err := service.repository.CurrentMLBatch(ctx)
	if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
		return domain.PrevisoesResult{}, errs.New(errs.KindCurrentGoldBatchNotReady)
	}
	if err != nil {
		return domain.PrevisoesResult{}, wrapRepositoryError("get current ML batch", err)
	}

	forecastMonth := time.Date(
		batch.DataThrough.Year(),
		batch.DataThrough.Month()+1,
		1,
		0,
		0,
		0,
		0,
		time.UTC,
	)
	publication, err := service.repository.FindCurrentPublication(
		ctx,
		batch.ID,
		batch.DataThrough,
		forecastMonth,
	)
	if errors.Is(err, repositories.ErrForecastPublicationNotFound) {
		return domain.PrevisoesResult{}, errs.New(errs.KindForecastNotReady)
	}
	if err != nil {
		return domain.PrevisoesResult{}, wrapRepositoryError("get current forecast publication", err)
	}

	bairrosExist, categoriasExist, err := service.repository.FiltersExist(
		ctx,
		filter.BairroIDs,
		filter.Categorias,
	)
	if err != nil {
		return domain.PrevisoesResult{}, wrapRepositoryError("validate forecast filters", err)
	}
	if !bairrosExist {
		return domain.PrevisoesResult{}, errs.New(errs.KindInvalidBairroFilter)
	}
	if !categoriasExist {
		return domain.PrevisoesResult{}, errs.New(errs.KindInvalidCategoriaFilter)
	}

	items, err := service.repository.ListForecastItems(ctx, publication, filter)
	if err != nil {
		return domain.PrevisoesResult{}, wrapRepositoryError("list forecast items", err)
	}

	return domain.PrevisoesResult{
		Publication: publication,
		Items:       items,
	}, nil
}
