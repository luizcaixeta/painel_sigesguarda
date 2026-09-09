package middleware

import (
	"crypto/rand"
	"net/http"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/requestcontext"
)

func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := rand.Text()
		w.Header().Set("X-Request-ID", requestID)

		ctx := requestcontext.WithRequestID(r.Context(), requestID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
