package router

import (
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/handler"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/middleware"
)

func New(
	readinessChecker handler.ReadinessChecker,
	bairroLister handler.BairroLister,
	queryTimeout time.Duration,
) http.Handler {
	mux := http.NewServeMux()

	registerGET(mux, "/healthz", http.HandlerFunc(handler.HealthCheckHandler))
	registerGET(
		mux,
		"/readyz",
		handler.NewReadinessHandler(readinessChecker, queryTimeout),
	)
	registerGET(
		mux,
		"/api/bairros",
		handler.NewBairrosHandler(bairroLister, queryTimeout),
	)
	mux.HandleFunc("/", handler.NotFoundHandler)

	return middleware.RequestID(mux)
}

func registerGET(mux *http.ServeMux, path string, routeHandler http.Handler) {
	mux.Handle("GET "+path, routeHandler)
	mux.HandleFunc("HEAD "+path, handler.MethodNotAllowedHandler)
	mux.HandleFunc(path, handler.MethodNotAllowedHandler)
}
