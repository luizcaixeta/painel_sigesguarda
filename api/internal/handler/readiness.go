package handler

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/database"
)

type ReadinessChecker interface {
	Check(context.Context) error
}

type ReadinessHandler struct {
	checker ReadinessChecker
	timeout time.Duration
}

type ReadinessResponse struct {
	Status string          `json:"status"`
	Checks ReadinessChecks `json:"checks"`
}

type ReadinessChecks struct {
	Database     string `json:"database"`
	DataContract string `json:"data_contract"`
}

func NewReadinessHandler(
	checker ReadinessChecker,
	timeout time.Duration,
) *ReadinessHandler {
	return &ReadinessHandler{
		checker: checker,
		timeout: timeout,
	}
}

func (handler *ReadinessHandler) ServeHTTP(
	w http.ResponseWriter,
	r *http.Request,
) {
	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	if err := handler.checker.Check(ctx); err != nil {
		code := "DATABASE_UNAVAILABLE"
		message := "database unavailable"
		if errors.Is(err, database.ErrDataNotReady) {
			code = "DATA_NOT_READY"
			message = "data contract unavailable"
		}

		WriteError(w, r, http.StatusServiceUnavailable, code, message)
		return
	}

	WriteJSON(w, http.StatusOK, ReadinessResponse{
		Status: "ready",
		Checks: ReadinessChecks{
			Database:     "ok",
			DataContract: "ok",
		},
	})
}
