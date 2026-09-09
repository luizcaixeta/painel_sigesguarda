package router

import (
	"net/http"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/handler"
)

func New() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /healthz", handler.HealthCheckHandler)

	return mux
}
