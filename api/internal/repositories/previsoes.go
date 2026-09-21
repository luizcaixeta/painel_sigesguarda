package repositories

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

var ErrForecastPublicationNotFound = errors.New("compatible forecast publication not found")

type PrevisaoRepository struct {
	pool *pgxpool.Pool
}

func NewPrevisaoRepository(pool *pgxpool.Pool) *PrevisaoRepository {
	return &PrevisaoRepository{pool: pool}
}

func (repository *PrevisaoRepository) CurrentMLBatch(
	ctx context.Context,
) (domain.CurrentBatch, error) {
	const query = `
		SELECT batch_id::text, data_through
		FROM gold.load_batches
		WHERE dataset = 'ml_features' AND is_current = true
	`

	var batch domain.CurrentBatch
	err := repository.pool.QueryRow(ctx, query).Scan(&batch.ID, &batch.DataThrough)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.CurrentBatch{}, ErrCurrentBatchNotFound
	}
	if err != nil {
		return domain.CurrentBatch{}, fmt.Errorf("query current ML batch: %w", err)
	}

	return batch, nil
}

func (repository *PrevisaoRepository) FindCurrentPublication(
	ctx context.Context,
	batchID string,
	dataThrough time.Time,
	forecastMonth time.Time,
) (domain.ForecastPublication, error) {
	const query = `
		WITH expected_pairs AS (
			SELECT DISTINCT occurrence.bairro, occurrence.categoria
			FROM gold.ocorrencias_mensais_ml_features AS occurrence
			WHERE occurrence.batch_id = $1::uuid
				AND occurrence.data = $2::date
		),
		valid_runs AS (
			SELECT
				run.forecast_run_id,
				run.gold_batch_id,
				batch.data_through,
				run.forecast_month,
				run.mlflow_model_name,
				run.model_alias,
				run.mlflow_run_id,
				run.generated_at
			FROM monthly_forecasts.forecast_runs AS run
			INNER JOIN gold.load_batches AS batch
				ON batch.batch_id = run.gold_batch_id
			WHERE run.gold_batch_id = $1::uuid
				AND batch.dataset = 'ml_features'
				AND batch.is_current = true
				AND batch.data_through = $2::date
				AND run.forecast_month = $3::date
				AND EXISTS (SELECT 1 FROM expected_pairs)
				AND NOT EXISTS (
					(SELECT expected.bairro, expected.categoria FROM expected_pairs AS expected)
					EXCEPT
					(
						SELECT forecast.bairro, forecast.categoria
						FROM monthly_forecasts.monthly_forecasts AS forecast
						WHERE forecast.forecast_run_id = run.forecast_run_id
					)
				)
				AND NOT EXISTS (
					(
						SELECT forecast.bairro, forecast.categoria
						FROM monthly_forecasts.monthly_forecasts AS forecast
						WHERE forecast.forecast_run_id = run.forecast_run_id
					)
					EXCEPT
					(SELECT expected.bairro, expected.categoria FROM expected_pairs AS expected)
				)
				AND NOT EXISTS (
					SELECT 1
					FROM monthly_forecasts.monthly_forecasts AS forecast
					LEFT JOIN gold.dim_bairros AS bairro
						ON replace(bairro.bairro_id, '-', ' ') = forecast.bairro
					WHERE forecast.forecast_run_id = run.forecast_run_id
						AND bairro.bairro_id IS NULL
				)
		)
		SELECT
			forecast_run_id::text,
			gold_batch_id::text,
			data_through,
			forecast_month,
			mlflow_model_name,
			model_alias,
			mlflow_run_id,
			generated_at
		FROM valid_runs
		ORDER BY generated_at DESC, forecast_run_id DESC
		LIMIT 1
	`

	var publication domain.ForecastPublication
	err := repository.pool.QueryRow(
		ctx,
		query,
		batchID,
		dataThrough,
		forecastMonth,
	).Scan(
		&publication.RunID,
		&publication.GoldBatchID,
		&publication.DataThrough,
		&publication.ForecastMonth,
		&publication.ModelName,
		&publication.ModelAlias,
		&publication.MLflowRunID,
		&publication.GeneratedAt,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.ForecastPublication{}, ErrForecastPublicationNotFound
	}
	if err != nil {
		return domain.ForecastPublication{}, fmt.Errorf("query current forecast publication: %w", err)
	}

	return publication, nil
}

func (repository *PrevisaoRepository) FiltersExist(
	ctx context.Context,
	bairroIDs []string,
	categorias []string,
) (bool, bool, error) {
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
		return false, false, fmt.Errorf("validate forecast filters: %w", err)
	}

	return bairrosExist, categoriasExist, nil
}

func (repository *PrevisaoRepository) ListForecastItems(
	ctx context.Context,
	publication domain.ForecastPublication,
	filter domain.PrevisoesFilter,
) ([]domain.Previsao, error) {
	const query = `
		SELECT
			bairro.bairro_id,
			forecast.categoria,
			$2::date,
			forecast.predicted_count
		FROM monthly_forecasts.monthly_forecasts AS forecast
		INNER JOIN gold.dim_bairros AS bairro
			ON replace(bairro.bairro_id, '-', ' ') = forecast.bairro
		WHERE forecast.forecast_run_id = $1::uuid
			AND (
				COALESCE(cardinality($3::text[]), 0) = 0
				OR bairro.bairro_id = ANY($3::text[])
			)
			AND (
				COALESCE(cardinality($4::text[]), 0) = 0
				OR forecast.categoria = ANY($4::text[])
			)
		ORDER BY
			bairro.nome ASC,
			bairro.bairro_id ASC,
			forecast.categoria ASC
	`

	rows, err := repository.pool.Query(
		ctx,
		query,
		publication.RunID,
		publication.ForecastMonth,
		filter.BairroIDs,
		filter.Categorias,
	)
	if err != nil {
		return nil, fmt.Errorf("query forecast items: %w", err)
	}
	defer rows.Close()

	items := make([]domain.Previsao, 0)
	for rows.Next() {
		var item domain.Previsao
		if err := rows.Scan(
			&item.BairroID,
			&item.Categoria,
			&item.Mes,
			&item.Quantidade,
		); err != nil {
			return nil, fmt.Errorf("scan forecast item: %w", err)
		}
		items = append(items, item)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate forecast items: %w", err)
	}

	return items, nil
}
