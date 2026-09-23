package handler

import (
	"net/http"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
)

func NotFoundHandler(w http.ResponseWriter, r *http.Request) {
	WriteError(w, r, errs.New(errs.KindRouteNotFound))
}

func MethodNotAllowedHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Allow", http.MethodGet)
	WriteError(w, r, errs.New(errs.KindMethodNotAllowed))
}
