package database

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrDataNotReady = errors.New("data contract is not ready")

var requiredRelations = []string{
	"gold.load_batches",
	"gold.dim_bairros",
	"gold.dim_categorias",
	"gold.dim_indicadores",
	"gold.ocorrencias_mensais_ml_features",
	"gold.indicadores_socioeconomicos_anuais",
	"monthly_forecasts.forecast_runs",
	"monthly_forecasts.monthly_forecasts",
}

type ReadinessChecker struct {
	pool *pgxpool.Pool
}

func NewReadinessChecker(pool *pgxpool.Pool) *ReadinessChecker {
	return &ReadinessChecker{pool: pool}
}

func (checker *ReadinessChecker) Check(ctx context.Context) error {
	if err := checker.pool.Ping(ctx); err != nil {
		return fmt.Errorf("ping database: %w", err)
	}

	const query = `
		SELECT COALESCE(bool_and(to_regclass(relation_name) IS NOT NULL), false)
		FROM unnest($1::text[]) AS required(relation_name)
	`

	var contractReady bool
	if err := checker.pool.QueryRow(ctx, query, requiredRelations).Scan(&contractReady); err != nil {
		return fmt.Errorf("check data contract: %w", err)
	}

	if !contractReady {
		return ErrDataNotReady
	}

	return nil
}
