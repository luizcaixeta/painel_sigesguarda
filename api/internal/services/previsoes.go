package services

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
)

var ErrForecastNotReady = errors.New("forecast publication not ready")

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
		return domain.PrevisoesResult{}, ErrDataNotReady
	}
	if err != nil {
		return domain.PrevisoesResult{}, fmt.Errorf("get current ML batch: %w", err)
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
		return domain.PrevisoesResult{}, ErrForecastNotReady
	}
	if err != nil {
		return domain.PrevisoesResult{}, fmt.Errorf("get current forecast publication: %w", err)
	}

	bairrosExist, categoriasExist, err := service.repository.FiltersExist(
		ctx,
		filter.BairroIDs,
		filter.Categorias,
	)
	if err != nil {
		return domain.PrevisoesResult{}, fmt.Errorf("validate forecast filters: %w", err)
	}
	if !bairrosExist {
		return domain.PrevisoesResult{}, ErrInvalidBairroFilter
	}
	if !categoriasExist {
		return domain.PrevisoesResult{}, ErrInvalidCategoriaFilter
	}

	items, err := service.repository.ListForecastItems(ctx, publication, filter)
	if err != nil {
		return domain.PrevisoesResult{}, fmt.Errorf("list forecast items: %w", err)
	}

	return domain.PrevisoesResult{
		Publication: publication,
		Items:       items,
	}, nil
}
