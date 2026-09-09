package repositories

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

type CategoriaRepository struct {
	pool *pgxpool.Pool
}

func NewCategoriaRepository(pool *pgxpool.Pool) *CategoriaRepository {
	return &CategoriaRepository{pool: pool}
}

func (repository *CategoriaRepository) ListCategorias(
	ctx context.Context,
) ([]domain.Categoria, error) {
	const query = `
		SELECT codigo, nome
		FROM gold.dim_categorias
		ORDER BY nome ASC, codigo ASC
	`

	rows, err := repository.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("query categorias: %w", err)
	}
	defer rows.Close()

	categorias := make([]domain.Categoria, 0, 6)
	for rows.Next() {
		var categoria domain.Categoria
		if err := rows.Scan(&categoria.Codigo, &categoria.Nome); err != nil {
			return nil, fmt.Errorf("scan categoria: %w", err)
		}
		categorias = append(categorias, categoria)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate categorias: %w", err)
	}

	return categorias, nil
}
