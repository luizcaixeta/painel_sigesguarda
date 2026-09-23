package services

import (
	"context"
	"errors"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
)

type OcorrenciaRepository interface {
	CurrentMLBatch(context.Context) (domain.CurrentBatch, error)
	FiltersExist(context.Context, []string, []string) (bool, bool, error)
	ListOcorrencias(
		context.Context,
		string,
		domain.OcorrenciasFilter,
	) ([]domain.Ocorrencia, error)
}

type OcorrenciaService struct {
	repository OcorrenciaRepository
}

func NewOcorrenciaService(repository OcorrenciaRepository) *OcorrenciaService {
	return &OcorrenciaService{repository: repository}
}

func (service *OcorrenciaService) ListOcorrencias(ctx context.Context, filter domain.OcorrenciasFilter) (domain.OcorrenciasResult, error) {
	batch, err := service.repository.CurrentMLBatch(ctx)
	if errors.Is(err, repositories.ErrCurrentBatchNotFound) {
		return domain.OcorrenciasResult{}, errs.New(errs.KindCurrentGoldBatchNotReady)
	}
	if err != nil {
		return domain.OcorrenciasResult{}, wrapRepositoryError("get current ML batch", err)
	}

	bairrosExist, categoriasExist, err := service.repository.FiltersExist(
		ctx,
		filter.BairroIDs,
		filter.Categorias,
	)
	if err != nil {
		return domain.OcorrenciasResult{}, wrapRepositoryError("validate filters", err)
	}
	if !bairrosExist {
		return domain.OcorrenciasResult{}, errs.New(errs.KindInvalidBairroFilter)
	}
	if !categoriasExist {
		return domain.OcorrenciasResult{}, errs.New(errs.KindInvalidCategoriaFilter)
	}

	if len(filter.Meses) == 0 && filter.De == nil {
		filter.Meses = []time.Time{batch.DataThrough}
	}

	ocorrencias, err := service.repository.ListOcorrencias(
		ctx,
		batch.ID,
		filter,
	)
	if err != nil {
		return domain.OcorrenciasResult{}, wrapRepositoryError("list occurrences", err)
	}

	return domain.OcorrenciasResult{
		DataThrough: batch.DataThrough,
		Items:       ocorrencias,
	}, nil
}
