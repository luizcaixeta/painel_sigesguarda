package repositories

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

var ErrCurrentBatchNotFound = errors.New("current Gold batch not found")

type OcorrenciaRepository struct {
	pool *pgxpool.Pool
}

func NewOcorrenciaRepository(pool *pgxpool.Pool) *OcorrenciaRepository {
	return &OcorrenciaRepository{pool: pool}
}

func (repository *OcorrenciaRepository) CurrentMLBatch(ctx context.Context) (domain.CurrentBatch, error) {
	const query = `
		SELECT batch_id::text, data_through
		FROM gold.load_batches
		WHERE dataset = 'ml_features' AND is_current = true
	`

	var batch domain.CurrentBatch
	err := repository.pool.QueryRow(ctx, query).Scan(
		&batch.ID,
		&batch.DataThrough,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.CurrentBatch{}, ErrCurrentBatchNotFound
	}
	if err != nil {
		return domain.CurrentBatch{}, fmt.Errorf("query current ML batch: %w", err)
	}

	return batch, nil
}

func (repository *OcorrenciaRepository) FiltersExist(ctx context.Context, bairroIDs []string, categorias []string) (bool, bool, error) {
	const query = `
		SELECT
			COALESCE(cardinality($1::text[]), 0) = 0
			OR (
				SELECT count(*)
				FROM gold.dim_bairros
				WHERE bairro_id = ANY($1::text[])
			) = cardinality($1::text[]),
			COALESCE(cardinality($2::text[]), 0) = 0
			OR (
				SELECT count(*)
				FROM gold.dim_categorias
				WHERE codigo = ANY($2::text[])
			) = cardinality($2::text[])
	`

	var bairrosExist bool
	var categoriasExist bool
	if err := repository.pool.QueryRow(
		ctx,
		query,
		bairroIDs,
		categorias,
	).Scan(&bairrosExist, &categoriasExist); err != nil {
		return false, false, fmt.Errorf("validate occurrence filters: %w", err)
	}

	return bairrosExist, categoriasExist, nil
}

func (repository *OcorrenciaRepository) ListOcorrencias(ctx context.Context, batchID string, filter domain.OcorrenciasFilter) ([]domain.Ocorrencia, error) {
	const query = `
		SELECT
			bairro.bairro_id,
			occurrence.categoria,
			occurrence.data,
			occurrence.y
		FROM gold.ocorrencias_mensais_ml_features AS occurrence
		INNER JOIN gold.dim_bairros AS bairro
			ON bairro.nome = occurrence.bairro
		WHERE occurrence.batch_id = $1::uuid
			AND (
				COALESCE(cardinality($2::text[]), 0) = 0
				OR bairro.bairro_id = ANY($2::text[])
			)
			AND (
				COALESCE(cardinality($3::text[]), 0) = 0
				OR occurrence.categoria = ANY($3::text[])
			)
			AND (
				COALESCE(cardinality($4::date[]), 0) = 0
				OR occurrence.data = ANY($4::date[])
			)
			AND ($5::date IS NULL OR occurrence.data >= $5::date)
			AND ($6::date IS NULL OR occurrence.data <= $6::date)
		ORDER BY
			occurrence.data ASC,
			bairro.nome ASC,
			bairro.bairro_id ASC,
			occurrence.categoria ASC
	`

	rows, err := repository.pool.Query(
		ctx,
		query,
		batchID,
		filter.BairroIDs,
		filter.Categorias,
		filter.Meses,
		filter.De,
		filter.Ate,
	)
	if err != nil {
		return nil, fmt.Errorf("query occurrences: %w", err)
	}
	defer rows.Close()

	ocorrencias := make([]domain.Ocorrencia, 0)
	for rows.Next() {
		var ocorrencia domain.Ocorrencia
		if err := rows.Scan(
			&ocorrencia.BairroID,
			&ocorrencia.Categoria,
			&ocorrencia.Mes,
			&ocorrencia.Quantidade,
		); err != nil {
			return nil, fmt.Errorf("scan occurrence: %w", err)
		}
		ocorrencias = append(ocorrencias, ocorrencia)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate occurrences: %w", err)
	}

	return ocorrencias, nil
}
