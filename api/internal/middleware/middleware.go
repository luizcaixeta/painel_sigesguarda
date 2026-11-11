package middleware

import (
	"crypto/rand"
	"fmt"
	"log/slog"
	"net/http"
	"runtime/debug"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/requestcontext"
)

func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := incomingRequestID(r)
		if requestID == "" {
			requestID = rand.Text()
		}
		w.Header().Set("X-Request-ID", requestID)

		ctx := requestcontext.WithRequestID(r.Context(), requestID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func incomingRequestID(r *http.Request) string {
	values := r.Header.Values("X-Request-ID")
	if len(values) != 1 || len(values[0]) == 0 || len(values[0]) > 128 {
		return ""
	}

	for _, character := range values[0] {
		if !isRequestIDCharacter(character) {
			return ""
		}
	}
	return values[0]
}

func isRequestIDCharacter(character rune) bool {
	return character >= 'a' && character <= 'z' ||
		character >= 'A' && character <= 'Z' ||
		character >= '0' && character <= '9' ||
		character == '.' || character == '_' || character == '-'
}

func SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		next.ServeHTTP(w, r)
	})
}

type recoveryResponseWriter struct {
	http.ResponseWriter
	written bool
}

func (writer *recoveryResponseWriter) WriteHeader(status int) {
	if writer.written {
		return
	}
	writer.written = true
	writer.ResponseWriter.WriteHeader(status)
}

func (writer *recoveryResponseWriter) Write(body []byte) (int, error) {
	if !writer.written {
		writer.WriteHeader(http.StatusOK)
	}
	return writer.ResponseWriter.Write(body)
}

func Recovery(writeError func(http.ResponseWriter, *http.Request, error), next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		writer := &recoveryResponseWriter{ResponseWriter: w}
		defer func() {
			if recovered := recover(); recovered != nil {
				slog.Error(
					"panic recovered",
					"method", r.Method,
					"path", r.URL.Path,
					"request_id", requestcontext.RequestID(r.Context()),
					"panic", recovered,
					"stack", string(debug.Stack()),
				)
				if !writer.written {
					writeError(writer, r, fmt.Errorf("recovered panic: %v", recovered))
				}
			}
		}()
		next.ServeHTTP(writer, r)
	})
}
