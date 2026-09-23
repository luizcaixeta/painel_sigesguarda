package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/requestcontext"
)

type ErrorResponse struct {
	Error APIError `json:"error"`
}

type APIError struct {
	Code      errs.Code `json:"code"`
	Message   string    `json:"message"`
	RequestID string    `json:"request_id"`
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
	err error,
) {
	definition := errs.Resolve(err)
	requestID := requestcontext.RequestID(r.Context())

	if definition.Status >= http.StatusInternalServerError {
		slog.Error(
			"request failed",
			"method", r.Method,
			"path", r.URL.Path,
			"status", definition.Status,
			"request_id", requestID,
			"error", err,
		)
	}

	WriteJSON(w, definition.Status, ErrorResponse{
		Error: APIError{
			Code:      definition.Code,
			Message:   definition.Message,
			RequestID: requestID,
		},
	})
}
