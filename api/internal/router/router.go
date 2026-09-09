package router

import (
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/handler"
)

func New(
	readinessChecker handler.ReadinessChecker,
	queryTimeout time.Duration,
) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /healthz", handler.HealthCheckHandler)
	mux.Handle(
		"GET /readyz",
		handler.NewReadinessHandler(readinessChecker, queryTimeout),
	)

	return mux
}
