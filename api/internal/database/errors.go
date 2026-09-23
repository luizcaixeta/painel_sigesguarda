package database

import (
	"context"
	"errors"
	"net"
	"strings"

	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/puddle/v2"
)

func IsUnavailable(err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, context.DeadlineExceeded) || errors.Is(err, puddle.ErrClosedPool) {
		return true
	}

	var connectError *pgconn.ConnectError
	if errors.As(err, &connectError) || pgconn.Timeout(err) || pgconn.SafeToRetry(err) {
		return true
	}

	var networkError net.Error
	if errors.As(err, &networkError) {
		return true
	}

	var postgresError *pgconn.PgError
	if !errors.As(err, &postgresError) {
		return false
	}

	return strings.HasPrefix(postgresError.Code, "08") ||
		strings.HasPrefix(postgresError.Code, "53") ||
		strings.HasPrefix(postgresError.Code, "58") ||
		postgresError.Code == "57P01" ||
		postgresError.Code == "57P02" ||
		postgresError.Code == "57P03"
}
