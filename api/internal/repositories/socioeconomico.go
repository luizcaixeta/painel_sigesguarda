package repositories

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

type SocioeconomicoRepository struct {
	pool *pgxpool.Pool
}

func NewSocioeconomicoRepository(pool *pgxpool.Pool) *SocioeconomicoRepository {
	return &SocioeconomicoRepository{pool: pool}
}

func (repository *SocioeconomicoRepository) CurrentSocioeconomicBatch(
	ctx context.Context,
) (domain.CurrentBatch, error) {
	const query = `
		SELECT batch_id::text, data_through
		FROM gold.load_batches
		WHERE dataset = 'socioeconomic_features' AND is_current = true
	`

	var batch domain.CurrentBatch
	err := repository.pool.QueryRow(ctx, query).Scan(&batch.ID, &batch.DataThrough)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.CurrentBatch{}, ErrCurrentBatchNotFound
	}
	if err != nil {
		return domain.CurrentBatch{}, fmt.Errorf("query current socioeconomic batch: %w", err)
	}

	return batch, nil
}

func (repository *SocioeconomicoRepository) LatestAnnualYear(
	ctx context.Context,
	batchID string,
) (int32, error) {
	const query = `
		SELECT ano
		FROM gold.indicadores_socioeconomicos_anuais
		WHERE batch_id = $1::uuid
		ORDER BY ano DESC
		LIMIT 1
	`

	var year int32
	err := repository.pool.QueryRow(ctx, query, batchID).Scan(&year)
	if errors.Is(err, pgx.ErrNoRows) {
		return 0, ErrCurrentBatchNotFound
	}
	if err != nil {
		return 0, fmt.Errorf("query latest socioeconomic year: %w", err)
	}

	return year, nil
}

func (repository *SocioeconomicoRepository) ListIndicadores(
	ctx context.Context,
) ([]domain.Indicador, error) {
	const query = `
		SELECT codigo, nome, unidade
		FROM gold.dim_indicadores
		ORDER BY ordem_exibicao ASC, codigo ASC
	`

	rows, err := repository.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("query indicadores: %w", err)
	}
	defer rows.Close()

	indicadores := make([]domain.Indicador, 0, 6)
	for rows.Next() {
		var indicador domain.Indicador
		if err := rows.Scan(&indicador.Codigo, &indicador.Nome, &indicador.Unidade); err != nil {
			return nil, fmt.Errorf("scan indicador: %w", err)
		}
		indicadores = append(indicadores, indicador)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate indicadores: %w", err)
	}

	return indicadores, nil
}

func (repository *SocioeconomicoRepository) FiltersExist(
	ctx context.Context,
	bairroIDs []string,
	indicadores []string,
) (bool, bool, error) {
	const query = `
		SELECT
			COALESCE(cardinality($1::text[]), 0) = 0
			OR (SELECT count(*) FROM gold.dim_bairros WHERE bairro_id = ANY($1::text[])) = cardinality($1::text[]),
			COALESCE(cardinality($2::text[]), 0) = 0
			OR (SELECT count(*) FROM gold.dim_indicadores WHERE codigo = ANY($2::text[])) = cardinality($2::text[])
	`

	var bairrosExist, indicadoresExist bool
	if err := repository.pool.QueryRow(ctx, query, bairroIDs, indicadores).Scan(
		&bairrosExist,
		&indicadoresExist,
	); err != nil {
		return false, false, fmt.Errorf("validate socioeconomic filters: %w", err)
	}

	return bairrosExist, indicadoresExist, nil
}

func (repository *SocioeconomicoRepository) ListIndicadorValores(
	ctx context.Context,
	batchID string,
	filter domain.IndicadoresFilter,
) ([]domain.IndicadorValor, error) {
	const query = `
		SELECT fact.bairro_id, indicator.codigo, fact.ano, value.valor, fact.tipo_estimativa
		FROM gold.indicadores_socioeconomicos_anuais AS fact
		INNER JOIN gold.dim_bairros AS bairro ON bairro.bairro_id = fact.bairro_id
		CROSS JOIN LATERAL (
			VALUES
				('RENDIMENTO_MEDIO_RESPONSAVEL_SM'::text, fact.rendimento_medio_responsavel_sm),
				('PCT_ALFABETIZACAO_15_MAIS'::text, fact.pct_alfabetizacao_15mais),
				('PCT_SEM_BANHEIRO_SANITARIO'::text, fact.pct_sem_banheiro_sanitario),
				('PCT_ESGOTAMENTO_PRECARIO'::text, fact.pct_esgotamento_precario),
				('PCT_SEM_REDE_GERAL_AGUA'::text, fact.pct_sem_rede_geral_agua),
				('PCT_LIXO_DESTINO_INADEQUADO'::text, fact.pct_lixo_destino_inadequado)
		) AS value(codigo, valor)
		INNER JOIN gold.dim_indicadores AS indicator ON indicator.codigo = value.codigo
		WHERE fact.batch_id = $1::uuid
			AND (COALESCE(cardinality($2::text[]), 0) = 0 OR fact.bairro_id = ANY($2::text[]))
			AND (COALESCE(cardinality($3::text[]), 0) = 0 OR indicator.codigo = ANY($3::text[]))
			AND (COALESCE(cardinality($4::integer[]), 0) = 0 OR fact.ano = ANY($4::integer[]))
			AND ($5::integer IS NULL OR fact.ano >= $5::integer)
			AND ($6::integer IS NULL OR fact.ano <= $6::integer)
		ORDER BY fact.ano ASC, indicator.ordem_exibicao ASC, indicator.codigo ASC,
			bairro.nome ASC, fact.bairro_id ASC
	`

	rows, err := repository.pool.Query(
		ctx,
		query,
		batchID,
		filter.BairroIDs,
		filter.Indicadores,
		filter.Anos,
		filter.De,
		filter.Ate,
	)
	if err != nil {
		return nil, fmt.Errorf("query indicator values: %w", err)
	}
	defer rows.Close()

	items := make([]domain.IndicadorValor, 0)
	for rows.Next() {
		var item domain.IndicadorValor
		if err := rows.Scan(
			&item.BairroID,
			&item.Indicador,
			&item.Ano,
			&item.Valor,
			&item.TipoEstimativa,
		); err != nil {
			return nil, fmt.Errorf("scan indicator value: %w", err)
		}
		items = append(items, item)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate indicator values: %w", err)
	}

	return items, nil
}

func (repository *SocioeconomicoRepository) ListIQV(
	ctx context.Context,
	batchID string,
	filter domain.IQVFilter,
) ([]domain.IQV, error) {
	const query = `
		SELECT fact.bairro_id, fact.ano, fact.iqv, fact.tipo_estimativa
		FROM gold.indicadores_socioeconomicos_anuais AS fact
		INNER JOIN gold.dim_bairros AS bairro ON bairro.bairro_id = fact.bairro_id
		WHERE fact.batch_id = $1::uuid
			AND (COALESCE(cardinality($2::text[]), 0) = 0 OR fact.bairro_id = ANY($2::text[]))
			AND (COALESCE(cardinality($3::integer[]), 0) = 0 OR fact.ano = ANY($3::integer[]))
			AND ($4::integer IS NULL OR fact.ano >= $4::integer)
			AND ($5::integer IS NULL OR fact.ano <= $5::integer)
		ORDER BY fact.ano ASC,
			CASE WHEN $6::text = 'asc' THEN fact.iqv END ASC,
			CASE WHEN $6::text = 'desc' THEN fact.iqv END DESC,
			bairro.nome ASC, fact.bairro_id ASC
	`

	rows, err := repository.pool.Query(
		ctx,
		query,
		batchID,
		filter.BairroIDs,
		filter.Anos,
		filter.De,
		filter.Ate,
		filter.Ordem,
	)
	if err != nil {
		return nil, fmt.Errorf("query IQV: %w", err)
	}
	defer rows.Close()

	items := make([]domain.IQV, 0)
	for rows.Next() {
		var item domain.IQV
		if err := rows.Scan(&item.BairroID, &item.Ano, &item.Valor, &item.TipoEstimativa); err != nil {
			return nil, fmt.Errorf("scan IQV: %w", err)
		}
		items = append(items, item)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate IQV: %w", err)
	}

	return items, nil
}
