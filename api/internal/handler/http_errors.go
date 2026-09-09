package handler

import "net/http"

func NotFoundHandler(w http.ResponseWriter, r *http.Request) {
	WriteError(
		w,
		r,
		http.StatusNotFound,
		"NOT_FOUND",
		"route not found",
	)
}

func MethodNotAllowedHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Allow", http.MethodGet)
	WriteError(
		w,
		r,
		http.StatusMethodNotAllowed,
		"METHOD_NOT_ALLOWED",
		"method not allowed",
	)
}
