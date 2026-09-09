package repositories

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

type BairroRepository struct {
	pool *pgxpool.Pool
}

func NewBairroRepository(pool *pgxpool.Pool) *BairroRepository {
	return &BairroRepository{pool: pool}
}

func (repository *BairroRepository) ListBairros(
	ctx context.Context,
) ([]domain.Bairro, error) {
	const query = `
		SELECT bairro_id, nome
		FROM gold.dim_bairros
		ORDER BY nome ASC, bairro_id ASC
	`

	rows, err := repository.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("query bairros: %w", err)
	}
	defer rows.Close()

	bairros := make([]domain.Bairro, 0, 75)
	for rows.Next() {
		var bairro domain.Bairro
		if err := rows.Scan(&bairro.ID, &bairro.Nome); err != nil {
			return nil, fmt.Errorf("scan bairro: %w", err)
		}
		bairros = append(bairros, bairro)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate bairros: %w", err)
	}

	return bairros, nil
}
