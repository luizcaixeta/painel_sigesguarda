package handler

import (
	"encoding/json"
	"net/http"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/requestcontext"
)

type ErrorResponse struct {
	Error APIError `json:"error"`
}

type APIError struct {
	Code      string `json:"code"`
	Message   string `json:"message"`
	RequestID string `json:"request_id"`
}

func WriteJSON(w http.ResponseWriter, status int, response any) {
	writeJSON(w, status, "application/json", response)
}

func WriteGeoJSON(w http.ResponseWriter, status int, response any) {
	writeJSON(w, status, "application/geo+json", response)
}

func writeJSON(
	w http.ResponseWriter,
	status int,
	contentType string,
	response any,
) {
	w.Header().Set("Content-Type", contentType)
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(response)
}

func WriteError(
	w http.ResponseWriter,
	r *http.Request,
	status int,
	code string,
	message string,
) {
	WriteJSON(w, status, ErrorResponse{
		Error: APIError{
			Code:      code,
			Message:   message,
			RequestID: requestcontext.RequestID(r.Context()),
		},
	})
}
