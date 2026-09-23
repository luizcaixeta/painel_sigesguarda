package services

import (
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/database"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
)

func wrapRepositoryError(operation string, cause error) error {
	kind := errs.KindInternal
	if database.IsUnavailable(cause) {
		kind = errs.KindDatabaseUnavailable
	}
	return errs.Wrap(kind, operation, cause)
}
